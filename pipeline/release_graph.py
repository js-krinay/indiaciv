"""Walk the local dependency syntax used by the unbundled atlas."""

import posixpath
import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit


EXCLUDED_PARTS = {"dev", "raw", "interim", ".cache", "cache", "caches", "sources", "soi"}
EXCLUDED_SUFFIXES = (".local.json", ".zip", ".pdf", ".shp", ".shx", ".dbf", ".gpkg")


class EntryPoint(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            ref = attrs.get("src")
        elif tag == "link" and set((attrs.get("rel") or "").lower().split()) & {
            "stylesheet", "icon", "modulepreload", "preload", "manifest",
        }:
            ref = attrs.get("href")
        else:
            return
        if ref:
            self.references.append(ref)


# Tokenize enough JS to keep quoted text, comments and regexes out of the
# dependency scan. Template substitutions are scanned as code.
JS_TOKEN = re.compile(r"""//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[\w$]+|\S""")
JS_REGEX = re.compile(r"""/(?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\[\n])+/[a-z]*""")
TEMPLATE_PART = re.compile(r"\\\\|\\[\s\S]|" + chr(96) + r"|\$\{")
REGEX_PREFIX = {"", "(", "[", "{", "=", ",", ":", "?", "!", "&", "|", ";", "return", ">"}


def javascript_tokens(text):
    def scan(start, substitution=False):
        previous = ""
        depth = 0
        while match := JS_TOKEN.search(text, start):
            token = match[0]
            start = match.end()
            if token.startswith(("//", "/*")):
                continue
            if token == "/" and previous in REGEX_PREFIX:
                literal = JS_REGEX.match(text, match.start())
                if literal:
                    start = literal.end()
                    token = "<regex>"
            if token == chr(96):
                yield "<template>"
                while part := TEMPLATE_PART.search(text, start):
                    start = part.end()
                    if part[0] == chr(96):
                        break
                    if part[0] == "${":
                        start = yield from scan(start, substitution=True)
                        yield "<template>"
            else:
                if substitution and token == "}" and depth == 0:
                    return start
                depth += (token == "{") - (token == "}")
                yield token
            previous = token
        return len(text)

    return list(scan(0))


def quoted(token):
    return token.startswith(("'", '"'))


def scan_imports(tokens, name):
    for i, token in enumerate(tokens):
        if token not in ("import", "export") or (i and tokens[i - 1] == "."):
            continue
        following = tokens[i + 1]
        if token == "import" and following == "(":
            if not quoted(tokens[i + 2]) or tokens[i + 3] not in (")", ","):
                raise ValueError(f"Computed dynamic import in {name}; use a literal path")
            yield tokens[i + 2][1:-1]
        elif token == "import" and quoted(following):
            yield following[1:-1]
        elif (token == "import" and following != ".") or following in ("*", "{"):
            # A local export list ends at its closing brace unless followed by
            # 'from'. Imports can have a default binding before the named list.
            for j in range(i + 1, len(tokens) - 1):
                part = tokens[j]
                if part == "from" and quoted(tokens[j + 1]):
                    yield tokens[j + 1][1:-1]
                    break
                if part in (";", "import", "export") or (
                    part == "}" and tokens[j + 1] != "from"
                ):
                    break


def javascript_imports(text, name):
    return scan_imports(javascript_tokens(text) + ["", "", ""], name)


CSS_REFERENCE = re.compile(
    r"""/\*[\s\S]*?\*/|@import\s+(?:"([^"]*)"|'([^']*)')|"""
    r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^\s"')]+))\s*\)|"""
    r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'""",
    re.IGNORECASE,
)


def references(text, name):
    suffix = PurePosixPath(name).suffix.lower()
    if suffix == ".html":
        parser = EntryPoint()
        parser.feed(text)
        yield from ((ref, name) for ref in parser.references)
    elif suffix == ".css":
        for match in CSS_REFERENCE.finditer(text):
            ref = next((part for part in match.groups() if part), None)
            if ref:
                yield ref, name
    elif suffix in (".js", ".mjs"):
        tokens = javascript_tokens(text) + ["", "", ""]
        for ref in scan_imports(tokens, name):
            if not ref.startswith(("./", "../", "/")) and not urlsplit(ref).scheme:
                raise ValueError(f"Bare module specifier {ref!r} in {name}")
            yield ref, name
        for i, token in enumerate(tokens):
            if token == "fetch" and tokens[i + 1] == "(" and quoted(tokens[i + 2]):
                if tokens[i + 3] in (")", ","):
                    yield tokens[i + 2][1:-1], "index.html"
            elif token == "new" and tokens[i + 1:i + 3] == ["URL", "("]:
                if quoted(tokens[i + 3]) and tokens[i + 4:i + 10] == [
                    ",", "import", ".", "meta", ".", "url",
                ]:
                    yield tokens[i + 3][1:-1], name


def local_path(ref, base):
    url = urlsplit(ref)
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    if "\\" in path:
        raise ValueError(f"Use forward slashes in {ref!r} from {base}")
    relative = path.lstrip("/") if path.startswith("/") else posixpath.join(
        posixpath.dirname(base), path
    )
    name = posixpath.normpath(relative)
    if name == ".." or name.startswith("../"):
        raise ValueError(f"Outside web root: {ref!r} from {base}")
    return name


def checked_input(web, name):
    parts = PurePosixPath(name.lower()).parts
    if (EXCLUDED_PARTS.intersection(parts)
            or any(part.startswith(("soi_", "soi-", ".")) for part in parts)
            or name.lower().endswith(EXCLUDED_SUFFIXES)):
        raise ValueError(f"Excluded release input: {name}")
    source = web / name
    if source.resolve() != web.resolve() / name:
        raise ValueError(f"Unexpected release input: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"Missing release input: {source}")
    return source


def dependency_graph(web, roots):
    found = set()
    pending = list(reversed(roots))
    while pending:
        name = pending.pop()
        if name in found:
            continue
        source = checked_input(web, name)
        found.add(name)
        if source.suffix.lower() in (".html", ".js", ".mjs", ".css"):
            for ref, base in references(source.read_text(encoding="utf-8"), name):
                dependency = local_path(ref, base)
                if dependency is not None:
                    pending.append(dependency)
    return found
