import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, toast } from "../api";
import WindowCanvas from "../components/WindowCanvas";
import { BarsView } from "../components/CutView";
import { CostEditor, CostSummary } from "../components/Cost";
import AddToQuote from "../components/AddToQuote";
import { Card, Field, Num, Tabs } from "../components/ui";
import { useHistory } from "../lib/useHistory";
import { Panel, toMm } from "../lib/window";
import { fmt } from "../lib/format";

const S = (type: Panel["type"], direction: Panel["direction"] = "left"): Panel => ({ type, direction });
const PRESETS: Record<string, any> = {
  "Sliding window, 2 panels": { system_code: "SLIDING-WIN-2T", width: 1800, height: 1200, panels: [S("sliding", "left"), S("sliding", "right")], glass_thickness: 6 },
  "Sliding window, 3 panels (2 + fixed)": { system_code: "SLIDING-WIN-2T", width: 2400, height: 1200, panels: [S("fixed"), S("sliding", "left"), S("sliding", "right")], glass_thickness: 6 },
  "Casement + fixed": { system_code: "CASEMENT-WIN", width: 1500, height: 1100, panels: [S("casement", "left"), S("fixed"), S("casement", "right")], glass_thickness: 5 },
  "Sliding door, 2 panels": { system_code: "SLIDING-DOOR", width: 1800, height: 2100, panels: [S("sliding", "left"), S("sliding", "right")], glass_thickness: 8 },
  "Hinged door, single": { system_code: "HINGED-DOOR", width: 900, height: 2100, panels: [S("casement", "right")], glass_thickness: 8 },
};
const FACTOR: any = { mm: 1, cm: 10, m: 1000, in: 25.4, ft: 304.8 };
const blank = () => ({ name: "Window 1", unit: "mm", frame_mm: 50, mullion_mm: 40, transoms: 0, quantity: 1, ...PRESETS["Sliding window, 2 panels"] });

export default function AluminiumDesigner() {
  const loc: any = useLocation();
  const h = useHistory<any>(blank());
  const d = h.state;
  const [systems, setSystems] = useState<any[]>([]);
  const [cost, setCost] = useState<any>(null);
  const [sel, setSel] = useState<number | null>(null);
  const [snap, setSnap] = useState(50);
  const [grid, setGrid] = useState(true);
  const [calc, setCalc] = useState<any>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState("Cut list");
  const [productId, setProductId] = useState<number | null>(null);
  const [currency, setCurrency] = useState("LKR");

  useEffect(() => {
    api("/api/systems").then(setSystems);
    api("/api/settings").then((s) => { setCurrency(s.general.currency); setCost((c: any) => c ?? s.cost_aluminium); });
  }, []);
  useEffect(() => {
    const p = loc.state?.product;
    if (p?.kind === "aluminium") { h.reset({ ...p.params, name: p.name, system_code: p.system_code, quantity: p.params.quantity ?? 1 }); if (p.cost) setCost(p.cost); setProductId(p.id); }
  }, [loc.state]);

  const f = FACTOR[d.unit];
  const params = useMemo(() => ({ width: d.width, height: d.height, unit: d.unit, glass_thickness: d.glass_thickness, frame_mm: d.frame_mm, mullion_mm: d.mullion_mm, transoms: d.transoms, panels: d.panels }), [d]);
  const valid = d.width > 0 && d.height > 0 && d.panels.length > 0 && cost;

  useEffect(() => {
    if (!valid) { setCalc(null); return; }
    let dead = false;
    const t = setTimeout(async () => {
      try {
        const r = await api("/api/calc/item", { body: { kind: "aluminium", params, system_code: d.system_code, cost, quantity: d.quantity } });
        if (!dead) { setCalc(r); setErr(""); }
      } catch (e: any) { if (!dead) { setErr(e.message); setCalc(null); } }
    }, 300);
    return () => { dead = true; clearTimeout(t); };
  }, [JSON.stringify(params), d.system_code, JSON.stringify(cost), d.quantity]);

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === "INPUT" || (e.target as HTMLElement).tagName === "SELECT") return;
      if (e.ctrlKey && e.key === "z") { e.preventDefault(); h.undo(); }
      if (e.ctrlKey && (e.key === "y" || (e.shiftKey && e.key === "Z"))) { e.preventDefault(); h.redo(); }
      if ((e.key === "Delete" || e.key === "Backspace") && sel !== null) removePanel(sel);
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  });

  const up = (patch: any) => h.set({ ...d, ...patch });
  const setPanel = (i: number, patch: Partial<Panel>) => up({ panels: d.panels.map((p: Panel, j: number) => (j === i ? { ...p, ...patch } : p)) });
  const addPanel = () => d.panels.length < 8 && up({ panels: [...d.panels, S("sliding", "left")] });
  const removePanel = (i: number) => { if (d.panels.length > 1) { up({ panels: d.panels.filter((_: any, j: number) => j !== i) }); setSel(null); } };
  const changeUnit = (u: string) => up({ unit: u, width: +(d.width * f / FACTOR[u]).toFixed(u === "mm" ? 0 : 3), height: +(d.height * f / FACTOR[u]).toFixed(u === "mm" ? 0 : 3) });
  const sys = systems.find((s) => s.code === d.system_code);

  const save = async () => {
    try {
      const body = { name: d.name, kind: "aluminium", params: { ...params, quantity: d.quantity }, system_code: d.system_code, cost };
      if (productId) await api(`/api/products/${productId}`, { method: "PUT", body });
      else { const r = await api("/api/products", { body }); setProductId(r.id); }
      toast("Design saved to Products");
    } catch (e: any) { toast(e.message, "err"); }
  };
  const selP = sel !== null ? d.panels[sel] : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-xl font-semibold">Aluminium Designer</h1>
        <select className="inp w-auto" value="" onChange={(e) => { if (e.target.value) { h.set({ ...d, ...PRESETS[e.target.value] }); setSel(null); } }} aria-label="Templates">
          <option value="">Start from template…</option>{Object.keys(PRESETS).map((k) => <option key={k}>{k}</option>)}
        </select>
        <button className="btn" onClick={h.undo} disabled={!h.canUndo}>Undo</button>
        <button className="btn" onClick={h.redo} disabled={!h.canRedo}>Redo</button>
        <button className="btn" onClick={save}>Save design</button>
        <AddToQuote disabled={!calc} defaultName={d.name} quantity={d.quantity}
          build={() => ({ kind: "aluminium", params, system_code: d.system_code, cost })} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="min-w-0 space-y-3">
          <WindowCanvas widthMm={toMm(d.width || 1, d.unit)} heightMm={toMm(d.height || 1, d.unit)} panels={d.panels} transoms={d.transoms}
            frame={d.frame_mm} mullion={d.mullion_mm} selected={sel} onSelect={setSel} snap={snap} grid={grid} unit={d.unit}
            onResize={(w, hh) => up({ width: +(w / f).toFixed(d.unit === "mm" ? 0 : 3), height: +(hh / f).toFixed(d.unit === "mm" ? 0 : 3) })} />
          <p className="text-[12px] text-mute">Drag the blue handles to resize · click a panel to edit it · scroll to zoom · drag the background to pan · Delete removes the selected panel · Ctrl+Z / Ctrl+Y undo and redo.</p>
          {err && <div role="alert" className="rounded border border-bad p-3 text-bad">{err}</div>}
          {calc && (
            <Card>
              <Tabs tabs={["Cut list", "Cutting layout", "Glass & accessories", "Cost"]} value={tab} onChange={setTab} />
              <div className="pt-3">
                {tab === "Cut list" && (
                  <table className="w-full"><thead><tr><th className="th">Part</th><th className="th">Profile</th><th className="th num">Qty / unit</th><th className="th num">Cut length (mm)</th></tr></thead>
                    <tbody>{calc.cuts.map((c: any, i: number) => <tr key={i}><td className="td">{c.role}</td><td className="td font-mono">{c.profile}</td><td className="td num">{c.qty}</td><td className="td num">{fmt(c.length, 1)}</td></tr>)}</tbody></table>
                )}
                {tab === "Cutting layout" && (<>
                  <p className="mb-3 text-mute">Bars needed for the whole batch of {d.quantity} unit(s), including saw kerf and the profile's cutting allowance.</p>
                  <BarsView plans={calc.cutting} />
                </>)}
                {tab === "Glass & accessories" && (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <h3 className="mb-1 font-semibold">Glass ({calc.glass.code})</h3>
                      <p>{calc.glass.qty} pane(s) of <b>{fmt(calc.glass.width_mm, 1)} × {fmt(calc.glass.height_mm, 1)} mm</b></p>
                      <p className="text-mute">{fmt(calc.glass.area_sqm, 3)} m² per unit · glazing rubber {fmt(calc.glass.perimeter_mm / 1000, 2)} m</p>
                    </div>
                    <table className="w-full"><thead><tr><th className="th">Accessory</th><th className="th num">Qty / unit</th></tr></thead>
                      <tbody>{calc.accessories.map((a: any) => <tr key={a.code}><td className="td">{a.name}</td><td className="td num">{fmt(a.qty, 2)} {a.unit}</td></tr>)}</tbody></table>
                  </div>
                )}
                {tab === "Cost" && <CostSummary calc={calc} currency={currency} />}
              </div>
            </Card>
          )}
        </div>

        <aside className="space-y-3">
          <Card title="Measurements">
            <div className="grid grid-cols-2 gap-2">
              <Field label="Name" className="col-span-2"><input className="inp" value={d.name} onChange={(e) => up({ name: e.target.value })} /></Field>
              <Field label="System" className="col-span-2">
                <select className="inp" value={d.system_code} onChange={(e) => up({ system_code: e.target.value })}>
                  {systems.filter((s) => s.active).map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
                </select>
              </Field>
              <Field label="Unit"><select className="inp" value={d.unit} onChange={(e) => changeUnit(e.target.value)}>{["mm", "cm", "m", "in", "ft"].map((u) => <option key={u}>{u}</option>)}</select></Field>
              <Field label="Units to make"><Num value={d.quantity} min={1} step={1} onChange={(v) => up({ quantity: Math.max(1, Math.round(v || 1)) })} /></Field>
              <Field label={`Width (${d.unit})`}><Num value={d.width} min={0} onChange={(v) => up({ width: v })} /></Field>
              <Field label={`Height (${d.unit})`}><Num value={d.height} min={0} onChange={(v) => up({ height: v })} /></Field>
              <Field label="Glass thickness (mm)"><select className="inp" value={d.glass_thickness} onChange={(e) => up({ glass_thickness: +e.target.value })}>{[5, 6, 8].map((t) => <option key={t}>{t}</option>)}</select></Field>
              <Field label="Horizontal divisions"><Num value={d.transoms} min={0} max={5} step={1} onChange={(v) => up({ transoms: Math.min(5, Math.max(0, Math.round(v || 0))) })} /></Field>
              <Field label="Frame section (mm)"><Num value={d.frame_mm} min={20} onChange={(v) => up({ frame_mm: v })} /></Field>
              <Field label="Mullion section (mm)"><Num value={d.mullion_mm} min={10} onChange={(v) => up({ mullion_mm: v })} /></Field>
            </div>
            {sys && <p className="mt-2 text-[12px] text-mute">Formulas come from the “{sys.name}” system (Settings → Systems).</p>}
          </Card>
          <Card title={`Panels (${d.panels.length})`} actions={<button className="btn btn-sm" onClick={addPanel} disabled={d.panels.length >= 8}>Add panel</button>}>
            <ul className="space-y-1">
              {d.panels.map((p: Panel, i: number) => (
                <li key={i} className={`flex items-center gap-2 rounded border px-2 py-1 ${sel === i ? "border-accent bg-sunk" : "border-line"}`} onClick={() => setSel(i)}>
                  <span className="w-6 text-mute">{i + 1}</span>
                  <select className="inp py-1" value={p.type} aria-label={`Panel ${i + 1} type`} onChange={(e) => setPanel(i, { type: e.target.value as any })}>
                    <option value="sliding">Sliding</option><option value="fixed">Fixed glass</option><option value="casement">Casement / hinged</option>
                  </select>
                  <select className="inp w-24 py-1" value={p.direction} disabled={p.type === "fixed"} aria-label={`Panel ${i + 1} direction`} onChange={(e) => setPanel(i, { direction: e.target.value as any })}>
                    <option value="left">Left</option><option value="right">Right</option>
                  </select>
                  <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); removePanel(i); }} disabled={d.panels.length === 1} aria-label={`Delete panel ${i + 1}`}>×</button>
                </li>
              ))}
            </ul>
            {selP && <p className="mt-2 text-[12px] text-mute">Panel {sel! + 1} selected on the canvas.</p>}
          </Card>
          <Card title="Canvas">
            <div className="grid grid-cols-2 gap-2">
              <Field label="Snap to grid"><select className="inp" value={snap} onChange={(e) => setSnap(+e.target.value)}>{[0, 10, 25, 50, 100].map((s) => <option key={s} value={s}>{s ? `${s} mm` : "Off"}</option>)}</select></Field>
              <Field label="Grid"><select className="inp" value={grid ? 1 : 0} onChange={(e) => setGrid(e.target.value === "1")}><option value={1}>Show</option><option value={0}>Hide</option></select></Field>
            </div>
          </Card>
          <Card title="Labour, overhead and profit">{cost && <CostEditor cost={cost} onChange={setCost} />}</Card>
          {calc && <Card><div className="text-[12px] text-mute">Selling price per unit</div><div className="text-2xl font-semibold">{currency} {fmt(calc.summary.selling_price)}</div><div className="text-mute">× {d.quantity} = {currency} {fmt(calc.summary.selling_price * d.quantity)}</div></Card>}
        </aside>
      </div>
    </div>
  );
}
