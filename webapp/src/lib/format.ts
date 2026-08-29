export function fmtMoney(value: string | number): string {
  const n = Math.round(Number(value));
  return n.toLocaleString("en-US").replace(/,/g, " ");
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
