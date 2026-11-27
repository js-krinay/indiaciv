// Original painted silhouettes in the shared wonder plinth coordinate system.
const ivory = ["#f5e4bf", "#ad987d"];
const sandstone = ["#e9a178", "#a95646"];
const stone = ["#c4b697", "#796b62"];
const basalt = ["#a5a5a0", "#525369"];

function shape(g, path, light, shade = light, outline = true) {
  const p = new Path2D(path);
  const wash = g.createLinearGradient(-0.75, -1, 0.65, 0.4);
  wash.addColorStop(0, light);
  wash.addColorStop(1, shade);
  g.fillStyle = wash;
  g.fill(p);
  if (outline) {
    g.lineWidth = 0.035;
    g.strokeStyle = "#322932";
    g.lineJoin = "round";
    g.stroke(p);
  }
}

function block(g, x, y, w, h, colors) {
  shape(g, `M${x} ${y}h${w}v${h}h${-w}Z`, ...colors);
}

function arch(g, x, y, w, h, colors = ["#634755", "#372e38"]) {
  shape(g, `M${x} ${y}v${-h * 0.62}q${w / 2} ${-h * 0.78} ${w} 0v${h * 0.62}Z`, ...colors);
}

function towers(g, xs, height, colors) {
  for (const x of xs) {
    shape(g, `M${x - 0.08} .37l.024 ${-height}h.112l.024 ${height}Z`, ...colors);
    arch(g, x - 0.082, 0.37 - height, 0.164, 0.19, colors);
    block(g, x - 0.087, 0.62 - height, 0.174, 0.045, colors);
  }
}

function dome(g, x, y, width, height, colors) {
  shape(g, `M${x - width / 2} ${y}q${-width * 0.12} ${-height * 0.52} ${width / 2} ${-height}
    q${width * 0.62} ${height * 0.48} ${width / 2} ${height}Z`, ...colors);
}

function tomb(g, taj) {
  const colors = taj ? ivory : sandstone;
  if (taj) towers(g, [-0.81, -0.61, 0.61, 0.81], 1.17, ivory);
  block(g, -0.69, 0.28, 1.38, 0.12, colors);
  shape(g, "M-.64 .28v-.56l.14-.13h1l.14 .13v.56Z", ...colors);
  dome(g, 0, -0.4, 0.71, 0.69, taj ? ivory : ["#f1d4a3", "#ab7e64"]);
  block(g, -0.023, -1.22, 0.046, 0.14, ["#ecd28c", "#936e4b"]);
  for (const x of [-0.51, 0.36]) arch(g, x, 0.27, 0.15, 0.43);
  arch(g, -0.2, 0.28, 0.4, 0.66);
}

function tieredTemple(g, mode) {
  const colors = mode === "deccan" ? stone : sandstone;
  block(g, -0.84, 0.25, 1.68, 0.13, colors);
  block(g, -0.75, -0.08, 1.5, 0.34, colors);
  for (let i = 0; i < 5; i++) {
    const half = mode === "north" ? 0.46 - i * i * 0.016 : 0.62 - i * 0.11;
    const y = -0.1 - i * 0.19;
    shape(g, `M${-half - 0.055} ${y}l.07 -.18h${2 * half - 0.03}l.07 .18Z`, ...colors);
    for (const dx of [-0.56, 0, 0.56]) arch(g, dx * half - 0.04, y - 0.025, 0.08, 0.12);
  }
  dome(g, 0, -1.04, 0.3, 0.19, colors);
  arch(g, -0.14, 0.26, 0.28, 0.39);
}

function arches(g, variant) {
  const colors = variant === "gateway-of-india" ? ["#edcc99", "#a77a5d"] : stone;
  if (variant !== "india-gate") towers(g, [-0.65, 0.65], 1.42, colors);
  shape(g, "M-.68 .34h.24v-.56Q0-.83 .44-.22v.56h.24v-1.12h-.14v-.18H.4v-.17h-.8v.17h-.14v.18h-.14Z", ...colors);
  block(g, -0.59, -0.89, 1.18, 0.11, colors);
  block(g, -0.41, -1.14, 0.82, 0.09, colors);
}

function palace(g, hawa) {
  const colors = hawa ? ["#faac8e", "#bb6461"] : sandstone;
  for (let i = 0; i < (hawa ? 5 : 3); i++) {
    const half = 0.84 - i * 0.105;
    const y = 0.35 - i * 0.28;
    block(g, -half, y - 0.27, 2 * half, 0.28, colors);
    const n = hawa ? 7 - i : 3;
    for (let j = 0; j < n; j++) {
      const x = (j - (n - 1) / 2) * half * 1.7 / n;
      arch(g, x - 0.055, y - 0.06, 0.11, 0.18);
      block(g, x - 0.08, y - 0.06, 0.16, 0.035, ivory);
    }
  }
  dome(g, 0, hawa ? -1.04 : -0.49, 0.29, 0.15, colors);
}

function cliff(g, colors = basalt) {
  shape(g, "M-.95 .29l.12-.52 .4-.63 .54-.1 .49 .24 .3 .58 .06 .43Z", ...colors);
  shape(g, "M-.83-.23l.4-.63 .54-.1-.2 .52-.42 .33Z", "#c1aa95", "#807a76");
}

function lake(g, variant) {
  shape(g, "M-.96 .16l.21-.53 .54-.24 .61 .05 .45 .36 .09 .42-.55 .18-.72-.01Z", "#b7bf7a", "#586c4c");
  shape(g, "M-.79 .13l.2-.38 .4-.2 .53 .03 .36 .29 .09 .31-.5 .12-.62-.02Z", "#9fd9cc", "#31788b");
  for (const [x, y] of [[-.43, -.11], [-.11, .11], [.19, -.17], [.42, .03]]) {
    shape(g, `M${x} ${y}l.24-.025-.06 .045Z`, "#e4f2d1", "#b1e2cb", false);
  }
  if (variant === "wetland" || variant === "mangrove") {
    for (const [x, h] of [[-.65, .45], [-.32, .26], [.35, .39], [.63, .58]]) {
      shape(g, `M${x} .18l-.09 ${-h} .14 .19 .11-.15-.1 ${h - 0.04}Z`, "#c0c082", "#395f44");
      if (variant === "mangrove") dome(g, x, 0.18 - h, 0.38, 0.27, ["#8ab16a", "#395e48"]);
    }
  }
}

export const INDIA_WONDERS = {
  "Taj Mahal": ["taj-mahal", (g) => tomb(g, true)],
  "Domed tomb": ["domed-tomb", (g) => tomb(g, false)],
  "Statue of Unity": ["statue-of-unity", (g) => {
    block(g, -0.47, 0.17, 0.94, 0.2, stone);
    shape(g, "M-.3 .18l.07-.51-.04-.35 .04-.24 .15-.08 .03-.18 .1-.08 .09 .06 .02 .2 .15 .09 .04 .37-.1 .07 .04 .65H.03l-.08-.34-.08 .34Z", "#e0ae6f", "#855741");
    shape(g, "M-.22-.69l.16 .33-.11 .46-.08 .07 .04-.46Z M.13-.91l.1 .17-.01 .55-.1-.08Z", "#a1704e", "#694d41", false);
  }],
  "Jatayu": ["jatayu", (g) => {
    shape(g, "M-.93 .09l.05-.44 .21-.5 .17-.1-.05 .42 .26-.16 .14 .03-.04 .31 .38-.11 .17-.19 .2-.08 .21 .12 .19 .04-.23 .15-.19-.02-.11 .29-.4 .31-.56 .05Z", "#e7bc86", "#916650");
    for (let i = 0; i < 5; i++) shape(g, `M${-0.87 + i * 0.115} ${-0.28 + i * 0.065}l.28 .23 .04 .18-.23-.15Z`, ...sandstone);
    block(g, 0.58, -0.57, 0.055, 0.05, ["#312833"]);
  }],
  "India Gate": ["india-gate", (g) => arches(g, "india-gate")],
  "Gateway of India": ["gateway-of-india", (g) => arches(g, "gateway-of-india")],
  Charminar: ["charminar", (g) => {
    towers(g, [-0.45, 0.52], 1.44, stone);
    shape(g, "M-.6 .33v-.66l.22-.24h.92l.14 .19v.71H.2v-.43Q0-.49-.23-.1v.43Z", ...ivory);
    block(g, -0.61, -0.61, 1.3, 0.11, stone);
    for (const x of [-0.43, -0.22, -0.01, 0.2, 0.41]) arch(g, x, -0.32, 0.12, 0.18);
    towers(g, [-0.64, 0.64], 1.51, ivory);
  }],
  "Hawa Mahal": ["hawa-mahal", (g) => palace(g, true)],
  "Sandstone palace": ["palace", (g) => palace(g, false)],
  Kailash: ["kailash", (g) => {
    shape(g, "M-.95 .34l.3-.45 .2-.53 .33-.45 .28-.07 .3 .17 .17 .45 .31 .5-.02 .38Z", "#e6edf1", "#798596");
    shape(g, "M.16-1.16l.3 .17 .17 .45 .31 .5-.15 .25-.44-.35-.1-.48Z", "#b2b7c8", "#596777");
    shape(g, "M-.45-.64l.33-.45 .28-.07 .07 .46-.18 .07-.08 .42-.1-.41-.4 .33Z M-.68-.01l.48-.25 .38-.08-.3 .21Z", "#fff9e6", "#c5d6e2", false);
  }],
  "Northern temple": ["temple-north", (g) => tieredTemple(g, "north")],
  "Southern vimana": ["vimana", (g) => tieredTemple(g, "south")],
  "Deccan temple": ["temple-deccan", (g) => tieredTemple(g, "deccan")],
  "Sikh shrine": ["sikh-shrine", (g) => {
    lake(g);
    block(g, -0.6, -0.48, 1.2, 0.69, ["#fff0a1", "#b67135"]);
    for (const x of [-0.48, -0.24, 0, 0.24, 0.48]) arch(g, x - 0.06, 0.16, 0.12, 0.43);
    dome(g, 0, -0.47, 0.66, 0.59, ["#ffe681", "#c17a34"]);
    for (const x of [-0.49, 0.49]) dome(g, x, -0.48, 0.22, 0.28, ["#ffdd7a", "#ad6c33"]);
  }],
  "Konark wheel": ["konark-wheel", (g) => {
    block(g, -0.74, 0.19, 1.48, 0.17, stone);
    shape(g, "M-.68-.49a.68 .68 0 1 0 1.36 0 .68 .68 0 1 0-1.36 0 M-.52-.49a.52 .52 0 1 1 1.04 0 .52 .52 0 1 1-1.04 0", ...sandstone);
    for (let i = 0; i < 8; i++) {
      g.save();
      g.translate(0, -0.49);
      g.rotate(i * Math.PI / 4);
      block(g, -0.055, -0.57, 0.11, 0.57, stone);
      g.restore();
    }
    dome(g, 0, -0.36, 0.32, 0.29, sandstone);
  }],
  "Fort rampart": ["rampart", (g) => {
    shape(g, "M-.9 .3l.18-.44 1.21-.12 .42 .57Z", ...stone);
    block(g, -0.73, -0.47, 1.46, 0.6, sandstone);
    for (let i = 0; i < 7; i++) block(g, -0.72 + i * 0.218, -0.6, 0.13, 0.18, sandstone);
    for (const x of [-0.74, 0.49]) block(g, x, -0.85, 0.25, 1.11, stone);
    arch(g, -0.17, 0.19, 0.34, 0.52);
  }],
  Stupa: ["stupa", (g) => {
    block(g, -0.8, 0.17, 1.6, 0.18, stone);
    dome(g, 0, 0.17, 1.25, 0.92, stone);
    block(g, -0.06, -1.14, 0.12, 0.44, stone);
    for (const y of [-1.04, -0.96, -0.88]) block(g, -0.21, y, 0.42, 0.045, sandstone);
    for (const x of [-0.36, 0.22]) block(g, x, -0.17, 0.12, 0.51, ivory);
    block(g, -0.42, -0.2, 0.84, 0.095, ivory);
  }],
  Basilica: ["basilica", (g) => {
    block(g, -0.76, -0.41, 1.52, 0.74, sandstone);
    shape(g, "M-.51 .33v-1.06L0-1.08l.51 .35V.33Z", ...sandstone);
    for (const x of [-0.35, 0.22]) block(g, x, -0.67, 0.09, 0.98, ivory);
    arch(g, -0.13, 0.32, 0.26, 0.46);
    arch(g, -0.09, -0.36, 0.18, 0.25);
    block(g, -0.034, -1.26, 0.068, 0.24, ivory);
    block(g, -0.11, -1.19, 0.22, 0.05, ivory);
  }],
  "Rock-cut cave": ["rock-cave", (g) => {
    cliff(g);
    arch(g, -0.57, 0.3, 1.25, 0.72);
    block(g, -0.6, -0.36, 1.22, 0.11, stone);
    for (const x of [-0.51, -0.19, 0.14, 0.46]) block(g, x, -0.25, 0.09, 0.56, stone);
  }],
  Stepwell: ["stepwell", (g) => {
    shape(g, "M-.91-.34l.32-.51h1.18l.32 .51-.17 .7H-.74Z", ...stone);
    for (let i = 0; i < 5; i++) {
      const inset = 0.85 - 0.14 * i;
      const y = -0.52 + 0.15 * i;
      shape(g, `M${-inset} ${y}h${inset * 2}l-.1 .12h${-inset * 2 + 0.2}Z`, ...sandstone);
    }
    block(g, -0.22, 0.26, 0.44, 0.1, ["#81aba6", "#396166"]);
  }],
  "Colonial civic building": ["civic", (g) => {
    block(g, -0.84, -0.5, 1.68, 0.86, ivory);
    shape(g, "M-.86-.49L0-.99l.86 .5Z", ...stone);
    for (let i = 0; i < 5; i++) {
      const x = -0.72 + 0.3 * i;
      arch(g, x + 0.08, 0.27, 0.17, 0.62);
      block(g, x, -0.43, 0.065, 0.75, ivory);
    }
  }],
  "Research campus": ["research-campus", (g) => {
    const brick = ["#bd795e", "#69483c"];
    const glass = ["#8ebbbb", "#385961"];
    block(g, -0.94, -0.34, 1.88, 0.69, brick);
    block(g, -0.34, -0.72, 0.68, 1.07, ivory);
    block(g, -0.38, -0.76, 0.76, 0.11, stone);
    for (const x of [-0.82, -0.58, 0.42, 0.66]) {
      block(g, x, -0.18, 0.15, 0.25, glass);
    }
    block(g, -0.18, -0.5, 0.36, 0.24, glass);
    arch(g, 0, 0.34, 0.28, 0.43);
    block(g, -0.43, 0.34, 0.86, 0.08, stone);
  }],
  Minaret: ["minaret", (g) => {
    shape(g, "M-.36 .36l.24-1.52h.24l.24 1.52Z", ...sandstone);
    for (const [y, w] of [[-1.13, .16], [-.84, .2], [-.49, .25], [-.12, .3]]) block(g, -w, y, 2 * w, 0.075, ivory);
    dome(g, 0, -1.14, 0.25, 0.15, stone);
  }],
  Railway: ["railway", (g) => {
    shape(g, "M-.99 .32l.33-.27h1.39l.26 .27Z", ...stone);
    block(g, -0.59, -0.29, 1.26, 0.41, ["#99b79c", "#435d53"]);
    block(g, -0.84, -0.64, 0.55, 0.77, ["#bc675f", "#6c3f50"]);
    block(g, 0.43, -0.54, 0.15, 0.27, basalt);
    for (const x of [-0.58, -0.19, 0.21, 0.59]) dome(g, x, 0.26, 0.22, 0.26, basalt);
  }],
  Ruins: ["ruins", (g) => {
    shape(g, "M-.92 .22l.26-.47 .85-.37 .75 .44-.22 .51-.79 .06Z", ...stone);
    shape(g, "M-.77 .05v-.29l.8-.31 .68 .39v.23L.03-.29Z", ...sandstone);
    shape(g, "M-.67 .31V.04l.76-.23 .46 .12v.2L.06 .04Z", ...sandstone);
  }],
  "Living root bridge": ["root-bridge", (g) => {
    cliff(g, stone);
    for (const y of [-0.63, -0.22]) {
      shape(g, `M-.82 ${y}Q0 ${y + 0.56} .82 ${y}q-.78 .75-1.64 .12Z`, "#c6ab72", "#594638");
      for (const x of [-.7, -.45, -.2, .05, .3, .55]) block(g, x, y - 0.02, 0.027, 0.29, stone);
    }
    for (const x of [-0.76, 0.76]) dome(g, x, -0.41, 0.46, 0.71, ["#a1bf73", "#42674b"]);
  }],
  Falls: ["falls", (g) => {
    cliff(g);
    shape(g, "M-.29-.72l.61-.03-.12 .29 .05 .33 .41 .39-.39 .14-.68-.11 .26-.52Z", "#effaf4", "#66aeb7");
    shape(g, "M-.09-.68l.19-.01-.11 .4 .09 .31-.27 .25Z", "#c6f1eb", "#4998ac");
  }],
  Lake: ["lake", lake],
  Wetland: ["wetland", (g) => lake(g, "wetland")],
  Mangroves: ["mangrove", (g) => lake(g, "mangrove")],
  "Salt desert": ["salt-flat", (g) => {
    shape(g, "M-.99 .19l.4-.55 .91-.12 .63 .57-.23 .24-.97 .07Z", "#fff8e2", "#cbb4a6");
    shape(g, "M-.9 .17l.62-.15 .35 .25 .37-.35 .47 .15-.44-.09-.39 .33-.37-.24Z", "#aa8f89", "#ac989e", false);
  }],
  Volcano: ["volcano", (g) => {
    lake(g);
    shape(g, "M-.72 .09l.43-.46 .14-.5 .51-.02 .12 .41 .25 .57-.53 .16Z", ...basalt);
    shape(g, "M-.15-.87l.51-.02-.16 .19-.22-.02Z", "#edbc84", "#a45744");
    shape(g, "M.19-.72l.06 .35 .23 .43-.16-.12-.17-.29Z", "#f3ab64", "#a3554c");
  }],
  "Basalt columns": ["basalt", (g) => {
    lake(g);
    for (const [x, y] of [[-.49, -.54], [-.18, -.91], [.15, -.81], [.43, -.48], [-.31, -.3], [0, -.48], [.26, -.24]]) {
      shape(g, `M${x} ${y}l.14-.07 .15 .08V.21l-.15 .09-.14-.07Z`, ...basalt);
      shape(g, `M${x} ${y}l.14-.07 .15 .08-.15 .08Z`, ...stone);
    }
  }],
  Valley: ["valley", (g) => {
    shape(g, "M-.95 .23l.2-.86 .32-.29 .47 .53 .33-.51 .3 .15 .3 .97-.56 .18-.73-.01Z", "#aebb80", "#4a6651");
    shape(g, "M.03-.39l.07 .19-.21 .19 .49 .26-.18 .11-.46-.33 .27-.24Z", "#b7dfd1", "#589ca3");
  }],
};
