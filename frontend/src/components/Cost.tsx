import { Field, Num } from "./ui";
import { fmt, money } from "../lib/format";

export function CostEditor({ cost, onChange }: { cost: any; onChange: (c: any) => void }) {
  const set = (k: string, v: any) => onChange({ ...cost, [k]: v });
  return (
    <div className="grid grid-cols-2 gap-2">
      <Field label="Labour per m² of product"><Num value={cost.labour_per_sqm} min={0} onChange={(v) => set("labour_per_sqm", v)} /></Field>
      <Field label="Labour fixed (per unit)"><Num value={cost.labour_fixed} min={0} onChange={(v) => set("labour_fixed", v)} /></Field>
      <Field label="Transport (per unit)"><Num value={cost.transport} min={0} onChange={(v) => set("transport", v)} /></Field>
      <Field label="Installation (per unit)"><Num value={cost.installation} min={0} onChange={(v) => set("installation", v)} /></Field>
      <Field label="Other charges (per unit)"><Num value={cost.other} min={0} onChange={(v) => set("other", v)} /></Field>
      <Field label="Overhead %"><Num value={cost.overhead_pct} min={0} onChange={(v) => set("overhead_pct", v)} /></Field>
      <Field label="Profit type">
        <select className="inp" value={cost.profit_mode} onChange={(e) => set("profit_mode", e.target.value)}>
          <option value="percent">Percentage</option><option value="fixed">Fixed amount</option>
        </select>
      </Field>
      <Field label={cost.profit_mode === "percent" ? "Profit %" : "Profit amount"}><Num value={cost.profit_value} min={0} onChange={(v) => set("profit_value", v)} /></Field>
    </div>
  );
}

const CAT: any = { raw_materials: "Raw materials", glass: "Glass", accessories: "Accessories & hardware", finishing: "Finishing", wastage: "Wastage" };

export function CostSummary({ calc, currency = "LKR" }: { calc: any; currency?: string }) {
  const s = calc.summary;
  const row = (l: string, v: number, strong = false) => (
    <tr key={l} className={strong ? "font-semibold" : ""}><td className="td">{l}</td><td className="td num">{fmt(v)}</td></tr>
  );
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <table className="w-full"><tbody>
          {Object.entries(s.by_category).filter(([, v]: any) => v > 0).map(([k, v]: any) => row(CAT[k] || k, v))}
          {row("Materials total", s.materials_total, true)}
          {row("Labour", s.labour)}
          {row("Transport", s.transport)}
          {row("Installation", s.installation)}
          {row("Other charges", s.other)}
          {row(`Overhead (${s.config.overhead_pct}%)`, s.overhead)}
          {row("Production cost", s.production_cost, true)}
          {row(s.config.profit_mode === "percent" ? `Profit (${s.config.profit_value}%)` : "Profit (fixed)", s.profit)}
          <tr className="bg-accent text-accent-ink"><td className="px-2 py-2 font-semibold">Selling price (per unit)</td><td className="px-2 py-2 num font-semibold">{money(s.selling_price, currency)}</td></tr>
        </tbody></table>
        <p className="mt-2 text-[12px] text-mute">Costs use the saved <b>purchase</b> prices; profit is added on top. Amounts in {currency}.</p>
      </div>
      <div className="max-h-80 overflow-auto">
        <table className="w-full text-[13px]">
          <thead><tr><th className="th">Material</th><th className="th num">Qty</th><th className="th">Unit</th><th className="th num">Price</th><th className="th num">Amount</th></tr></thead>
          <tbody>
            {calc.lines.map((l: any, i: number) => (
              <tr key={i} className={l.category === "wastage" ? "text-mute" : ""}>
                <td className="td">{l.code === l.description ? l.code : <><span className="font-mono">{l.code}</span> {l.description}</>}</td>
                <td className="td num">{fmt(l.quantity, 2)}</td><td className="td">{l.unit}</td>
                <td className="td num">{fmt(l.unit_price)}</td><td className="td num">{fmt(l.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
