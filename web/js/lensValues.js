// The pipeline validates the grid size and run bounds before release.
export function decodeLensValues(encoded, size) {
  if (Array.isArray(encoded)) return encoded;
  const { runs } = encoded;
  const values = Array(size).fill(null);
  let end = 0;
  for (let i = 0; i < runs.length; i += 3) {
    const start = end + runs[i];
    end = start + runs[i + 1];
    values.fill(runs[i + 2], start, end);
  }
  return values;
}
