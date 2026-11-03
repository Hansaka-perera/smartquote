export const money = (n: number, cur = "LKR") =>
  `${cur} ${(n ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const fmt = (n: number, d = 2) => (n ?? 0).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
export const today = () => new Date().toISOString().slice(0, 10);
