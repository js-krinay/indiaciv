export function compact(n) {
  if (n == null || Number.isNaN(n)) return "–";
  const a = Math.abs(n);
  if (a >= 1e12) return (n / 1e12).toFixed(a >= 1e13 ? 1 : 2) + "T";
  if (a >= 1e9) return (n / 1e9).toFixed(a >= 1e11 ? 0 : 1) + "B";
  if (a >= 1e6) return (n / 1e6).toFixed(a >= 1e8 ? 0 : 1) + "M";
  if (a >= 1e3) return (n / 1e3).toFixed(a >= 1e5 ? 0 : 1).replace(/\.0$/, "") + "K";
  return String(Math.round(n));
}

export const money = (n) => (n == null ? "–" : "$" + compact(n));
export const dollars = (n) => (n == null ? "–" : "$" + Math.round(n).toLocaleString("en-US"));
export const int = (n) => (n == null ? "–" : Math.round(n).toLocaleString("en-US"));
export const pct = (x, d = 1) => (x == null ? "–" : (x * 100).toFixed(d) + "%");

export function yieldValue(y, v) {
  if (y.scale && Number.isFinite(v)) {
    const points = v / y.scale;
    if (points > 0 && points < 0.01) return "<0.01";
    if (points < 10) return points.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    return compact(points);
  }
  return y.unit === "usd" ? money(v) : compact(v);
}

export function yieldDetails(y, value, meta) {
  if (!Number.isFinite(value)) return [y.period, "Data unavailable"].filter(Boolean).join(" · ");
  const number = (v) => v.toLocaleString("en-IN", { maximumFractionDigits: 3 });
  const real = y.unit === "INR" ? `₹${number(value)}` : `${number(value)} ${y.unit}`;
  const components = Object.entries(meta?.components || {})
    .filter(([, v]) => Number.isFinite(v))
    .map(([label, v]) => `${label} ${number(v)}`);
  return [real, meta?.derivation, y.period, meta?.estimated ? "IndiaCiv estimate" : "", meta?.coverage, ...components]
    .filter(Boolean).join(" · ");
}

export function popShort(n) {
  if (n >= 1e7) return Math.round(n / 1e6) + "M";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  return Math.round(n / 1e3) + "K";
}

export const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
