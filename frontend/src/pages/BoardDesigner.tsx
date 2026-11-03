import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, toast } from "../api";
import { SheetsView } from "../components/CutView";
import { CostEditor, CostSummary } from "../components/Cost";
import AddToQuote from "../components/AddToQuote";
import { Card, Field, Num, Tabs } from "../components/ui";
import { useHistory } from "../lib/useHistory";
import { fmt } from "../lib/format";

const KINDS = ["stool", "table", "drawer", "cupboard", "wardrobe", "kitchen_cabinet", "bookshelf", "custom"];
const SIZES: any = { stool: [350, 450, 350], table: [1500, 750, 800], drawer: [500, 150, 450], cupboard: [900, 1800, 450], wardrobe: [1200, 2100, 550], kitchen_cabinet: [800, 720, 560], bookshelf: [800, 1800, 300], custom: [900, 900, 450] };
const num = (v: any) => (typeof v === "string" && /^\s*\d+(\.\d+)?\s*$/.test(v) ? parseFloat(v) : v);
const newComp = (m: string) => ({ name: "New component", qty: "1", length: "", width: "", height: "", area_basis: "LW", material_code: m, edges_length: 0, edges_width: 0, finish: "none", finish_sides: 1, rotatable: true });

export default function BoardDesigner() {
  const loc: any = useLocation();
  const h = useHistory<any>({ name: "Cupboard", kind: "custom", unit: "mm", overall: { W: 900, H: 1800, D: 450 }, thickness_mm: 18, components: [], hardware: [], quantity: 1 });
  const d = h.state;
  const [mats, setMats] = useState<any[]>([]);
  const [cost, setCost] = useState<any>(null);
  const [calc, setCalc] = useState<any>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState("Components");
  const [productId, setProductId] = useState<number | null>(null);
  const [currency, setCurrency] = useState("LKR");
  const [shelves, setShelves] = useState(2);
  const [doors, setDoors] = useState(2);

  useEffect(() => {
    api("/api/materials").then(setMats);
    api("/api/settings").then((s) => { setCurrency(s.general.currency); setCost((c: any) => c ?? s.cost_board); });
  }, []);
  useEffect(() => {
    const p = loc.state?.product;
    if (p?.kind === "board") { h.reset({ ...p.params, name: p.name, quantity: p.params.quantity ?? 1 }); if (p.cost) setCost(p.cost); setProductId(p.id); }
  }, [loc.state]);

  const boards = mats.filter((m) => m.sheet_length_mm && m.active);
  const hw = mats.filter((m) => ["Hardware", "Screws", "Accessories"].includes(m.category) && m.active);
  const payload = useMemo(() => ({
    unit: d.unit, overall: d.overall, thickness_mm: d.thickness_mm, hardware: d.hardware.filter((x: any) => x.code && x.qty > 0),
    components: d.components.map((c: any) => ({ ...c, qty: num(c.qty), length: num(c.length), width: num(c.width), height: num(c.height) })),
  }), [d]);

  useEffect(() => {
    if (!cost || d.components.length === 0) { setCalc(null); setErr(""); return; }
    let dead = false;
    const t = setTimeout(async () => {
      try {
        const r = await api("/api/calc/item", { body: { kind: "board", params: payload, cost, quantity: d.quantity } });
        if (!dead) { setCalc(r); setErr(""); }
      } catch (e: any) { if (!dead) { setErr(e.message); setCalc(null); } }
    }, 350);
    return () => { dead = true; clearTimeout(t); };
  }, [JSON.stringify(payload), JSON.stringify(cost), d.quantity]);

  const up = (p: any) => h.set({ ...d, ...p });
  const setComp = (i: number, p: any) => up({ components: d.components.map((c: any, j: number) => (j === i ? { ...c, ...p } : c)) });
  const applyTemplate = async (kind: string) => {
    try {
      const comps = kind === "custom" ? [] : await api(`/api/calc/furniture-template/${kind}?shelves=${shelves}&doors=${doors}`);
      const [W, H, D] = SIZES[kind];
      h.set({ ...d, kind, unit: "mm", name: kind.replace("_", " ").replace(/^./, (c) => c.toUpperCase()), overall: { W, H, D }, components: comps });
    } catch (e: any) { toast(e.message, "err"); }
  };
  const save = async () => {
    try {
      const body = { name: d.name, kind: "board", params: { ...payload, quantity: d.quantity }, cost };
      if (productId) await api(`/api/products/${productId}`, { method: "PUT", body });
      else { const r = await api("/api/products", { body }); setProductId(r.id); }
      toast("Design saved to Products");
    } catch (e: any) { toast(e.message, "err"); }
  };
  const ov = (k: string, v: number) => up({ overall: { ...d.overall, [k]: v } });
  const defMat = boards.find((m) => m.code === "MDF-18")?.code ?? boards[0]?.code ?? "";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-xl font-semibold">Board Furniture Designer</h1>
        <button className="btn" onClick={h.undo} disabled={!h.canUndo}>Undo</button>
        <button className="btn" onClick={h.redo} disabled={!h.canRedo}>Redo</button>
        <button className="btn" onClick={save}>Save design</button>
        <AddToQuote disabled={!calc} defaultName={d.name} quantity={d.quantity} build={() => ({ kind: "board", params: payload, cost })} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[320px_1fr]">
        <aside className="space-y-3">
          <Card title="Furniture">
            <div className="grid grid-cols-2 gap-2">
              <Field label="Name" className="col-span-2"><input className="inp" value={d.name} onChange={(e) => up({ name: e.target.value })} /></Field>
              <Field label="Type" className="col-span-2">
                <select className="inp" value={d.kind} onChange={(e) => applyTemplate(e.target.value)}>{KINDS.map((k) => <option key={k} value={k}>{k.replace("_", " ")}</option>)}</select>
              </Field>
              <Field label="Shelves"><Num value={shelves} min={0} step={1} onChange={(v) => setShelves(Math.max(0, Math.round(v || 0)))} /></Field>
              <Field label="Doors"><Num value={doors} min={0} step={1} onChange={(v) => setDoors(Math.max(0, Math.round(v || 0)))} /></Field>
              <button className="btn col-span-2" onClick={() => applyTemplate(d.kind)}>Rebuild components from type</button>
              <Field label="Unit"><select className="inp" value={d.unit} onChange={(e) => up({ unit: e.target.value })}>{["mm", "cm", "m", "in", "ft"].map((u) => <option key={u}>{u}</option>)}</select></Field>
              <Field label="Units to make"><Num value={d.quantity} min={1} step={1} onChange={(v) => up({ quantity: Math.max(1, Math.round(v || 1)) })} /></Field>
              <Field label={`Width W (${d.unit})`}><Num value={d.overall.W} min={0} onChange={(v) => ov("W", v)} /></Field>
              <Field label={`Height H (${d.unit})`}><Num value={d.overall.H} min={0} onChange={(v) => ov("H", v)} /></Field>
              <Field label={`Depth D (${d.unit})`}><Num value={d.overall.D} min={0} onChange={(v) => ov("D", v)} /></Field>
              <Field label="Board thickness t (mm)"><Num value={d.thickness_mm} min={3} onChange={(v) => up({ thickness_mm: v })} /></Field>
            </div>
            <p className="mt-2 text-[12px] text-mute">Component sizes written as formulas (for example <span className="font-mono">W-2*t</span>) follow these overall measurements automatically.</p>
          </Card>
          <Card title="Hardware" actions={<button className="btn btn-sm" onClick={() => up({ hardware: [...d.hardware, { code: hw[0]?.code ?? "", qty: 1 }] })}>Add</button>}>
            {d.hardware.length === 0 && <p className="text-mute">No hinges, slides or handles added.</p>}
            {d.hardware.map((x: any, i: number) => (
              <div key={i} className="mb-1 flex gap-1">
                <select className="inp" value={x.code} aria-label="Hardware item" onChange={(e) => up({ hardware: d.hardware.map((y: any, j: number) => (j === i ? { ...y, code: e.target.value } : y)) })}>
                  {hw.map((m) => <option key={m.code} value={m.code}>{m.name}</option>)}
                </select>
                <div className="w-20"><Num value={x.qty} min={0} onChange={(v) => up({ hardware: d.hardware.map((y: any, j: number) => (j === i ? { ...y, qty: v } : y)) })} /></div>
                <button className="btn btn-sm btn-danger" aria-label="Remove hardware" onClick={() => up({ hardware: d.hardware.filter((_: any, j: number) => j !== i) })}>×</button>
              </div>
            ))}
          </Card>
          <Card title="Labour, overhead and profit">{cost && <CostEditor cost={cost} onChange={setCost} />}</Card>
          {calc && <Card><div className="text-[12px] text-mute">Selling price per unit</div><div className="text-2xl font-semibold">{currency} {fmt(calc.summary.selling_price)}</div><div className="text-mute">× {d.quantity} = {currency} {fmt(calc.summary.selling_price * d.quantity)}</div></Card>}
        </aside>

        <div className="min-w-0 space-y-3">
          <Card title="Components" actions={<button className="btn btn-sm" onClick={() => up({ components: [...d.components, newComp(defMat)] })}>Add component</button>}>
            {d.components.length === 0 ? <p className="text-mute">Pick a furniture type to load a starting component list, or add components one by one.</p> : (
              <div className="overflow-auto">
                <table className="w-full min-w-[980px] text-[13px]">
                  <thead><tr>{["Component", "Qty (T)", "Length (L)", "Width (W)", "Height (H)", "Area from", "Board", "Edge L", "Edge W", "Finish", "Sides", ""].map((t) => <th key={t} className="th">{t}</th>)}</tr></thead>
                  <tbody>
                    {d.components.map((c: any, i: number) => (
                      <tr key={i}>
                        <td className="td"><input className="inp" value={c.name} aria-label="Component name" onChange={(e) => setComp(i, { name: e.target.value })} /></td>
                        {["qty", "length", "width", "height"].map((k) => <td className="td w-24" key={k}><input className="inp" value={c[k] ?? ""} aria-label={k} onChange={(e) => setComp(i, { [k]: e.target.value })} /></td>)}
                        <td className="td"><select className="inp min-w-[84px]" value={c.area_basis} onChange={(e) => setComp(i, { area_basis: e.target.value })}><option value="LW">L × W</option><option value="LH">L × H</option><option value="WH">W × H</option></select></td>
                        <td className="td"><select className="inp min-w-[96px]" value={c.material_code} onChange={(e) => setComp(i, { material_code: e.target.value })}>{boards.map((m) => <option key={m.code} value={m.code}>{m.code}</option>)}</select></td>
                        <td className="td w-16"><select className="inp" value={c.edges_length} onChange={(e) => setComp(i, { edges_length: +e.target.value })}>{[0, 1, 2].map((n) => <option key={n}>{n}</option>)}</select></td>
                        <td className="td w-16"><select className="inp" value={c.edges_width} onChange={(e) => setComp(i, { edges_width: +e.target.value })}>{[0, 1, 2].map((n) => <option key={n}>{n}</option>)}</select></td>
                        <td className="td"><select className="inp min-w-[110px]" value={c.finish} onChange={(e) => setComp(i, { finish: e.target.value })}><option value="none">None</option><option value="paint">Spray paint</option><option value="laminate">Laminate</option><option value="polish">Polish</option></select></td>
                        <td className="td w-16"><select className="inp" value={c.finish_sides} onChange={(e) => setComp(i, { finish_sides: +e.target.value })}><option>1</option><option>2</option></select></td>
                        <td className="td"><button className="btn btn-sm btn-danger" aria-label="Delete component" onClick={() => up({ components: d.components.filter((_: any, j: number) => j !== i) })}>×</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="mt-2 text-[12px] text-mute">Plain numbers use the unit chosen on the left. Formulas (using W, H, D, t) are in millimetres. Edge columns count how many long / short edges get edge banding.</p>
          </Card>
          {err && <div role="alert" className="rounded border border-bad p-3 text-bad">{err}</div>}
          {calc && (
            <Card>
              <Tabs tabs={["Components", "Sheets", "Cutting layout", "Cost"]} value={tab} onChange={setTab} />
              <div className="pt-3">
                {tab === "Components" && (<>
                  <div className="mb-3 flex flex-wrap gap-6">
                    <div><div className="text-[12px] text-mute">Total board area (per unit)</div><div className="text-lg font-semibold">{fmt(calc.total_board_area_sqm, 3)} m² <span className="text-mute">({fmt(calc.total_board_area_sqft, 1)} ft²)</span></div></div>
                    {Object.entries(calc.area_by_thickness_mm).map(([t, a]: any) => <div key={t}><div className="text-[12px] text-mute">{t} mm boards</div><div className="text-lg font-semibold">{fmt(a, 3)} m²</div></div>)}
                  </div>
                  <table className="w-full text-[13px]"><thead><tr><th className="th">Component</th><th className="th num">Qty</th><th className="th num">Size (mm)</th><th className="th">Board</th><th className="th num">Area each (m²)</th><th className="th num">Area total (m²)</th><th className="th num">Edging (m)</th></tr></thead>
                    <tbody>{calc.components.map((c: any, i: number) => <tr key={i}><td className="td">{c.name}</td><td className="td num">{c.qty}</td><td className="td num">{fmt(c.length_mm, 0)} × {fmt(c.width_mm, 0)}</td><td className="td font-mono">{c.material_code}</td><td className="td num">{fmt(c.area_each_sqm, 4)}</td><td className="td num">{fmt(c.area_total_sqm, 4)}</td><td className="td num">{fmt(c.edge_banding_m, 2)}</td></tr>)}</tbody></table>
                </>)}
                {tab === "Sheets" && (<>
                  <p className="mb-2 text-mute">Theoretical = board area ÷ sheet area. Practical = sheets needed after arranging the pieces on the sheet (kerf {fmt(calc.sheets[Object.keys(calc.sheets)[0]]?.layout?.kerf ?? 3, 0)} mm). Pricing uses the “board charge mode” in Settings (currently {calc.charge_mode === "sheets" ? "practical sheets" : "area"}).</p>
                  <table className="w-full"><thead><tr><th className="th">Board</th><th className="th">Sheet size</th><th className="th num">Area (m²)</th><th className="th num">Theoretical (exact)</th><th className="th num">Theoretical (+ wastage)</th><th className="th num">Practical sheets</th><th className="th num">Utilisation</th></tr></thead>
                    <tbody>{Object.entries(calc.sheets).map(([code, s]: any) => <tr key={code}><td className="td"><span className="font-mono">{code}</span> {s.name}</td><td className="td">{s.sheet_size_mm[0]} × {s.sheet_size_mm[1]}</td><td className="td num">{fmt(s.area_sqm, 3)}</td><td className="td num">{fmt(s.theoretical_sheets_exact, 2)}</td><td className="td num">{s.theoretical_sheets_with_wastage}</td><td className="td num font-semibold">{s.practical_sheets}</td><td className="td num">{fmt(s.utilisation_pct, 1)}%</td></tr>)}</tbody></table>
                </>)}
                {tab === "Cutting layout" && <SheetsView sheets={calc.sheets} />}
                {tab === "Cost" && <CostSummary calc={calc} currency={currency} />}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
