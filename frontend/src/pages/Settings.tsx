import { useEffect, useState } from "react";
import { api, toast } from "../api";
import { Card, Field, Num, Tabs } from "../components/ui";
import { CostEditor } from "../components/Cost";

export default function Settings() {
  const [s, setS] = useState<any>(null);
  const [tab, setTab] = useState("Company");
  const [systems, setSystems] = useState<any[]>([]);
  const [sid, setSid] = useState<number | null>(null);
  const [json, setJson] = useState("");
  const load = () => { api("/api/settings").then(setS); api("/api/systems").then((r) => { setSystems(r); if (sid === null && r[0]) { setSid(r[0].id); setJson(JSON.stringify(r[0].config, null, 2)); } }); };
  useEffect(load, []);
  if (!s) return <p className="text-mute">Loading…</p>;
  const save = async (key: string) => { try { setS({ ...s, [key]: await api(`/api/settings/${key}`, { method: "PUT", body: { value: s[key] } }) }); toast("Settings saved"); } catch (e: any) { toast(e.message, "err"); } };
  const set = (key: string, k: string, v: any) => setS({ ...s, [key]: { ...s[key], [k]: v } });
  const sys = systems.find((x) => x.id === sid);
  const saveSystem = async () => {
    try { await api(`/api/systems/${sid}`, { method: "PUT", body: { code: sys.code, name: sys.name, kind: sys.kind, active: sys.active, config: JSON.parse(json) } }); toast("System saved"); load(); }
    catch (e: any) { toast(e instanceof SyntaxError ? "That is not valid JSON: " + e.message : e.message, "err"); }
  };
  const logo = async (f: File) => { const fd = new FormData(); fd.append("file", f); try { await api("/api/settings/logo", { form: fd }); toast("Logo uploaded"); load(); } catch (e: any) { toast(e.message, "err"); } };
  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-xl font-semibold">Settings</h1>
      <Tabs tabs={["Company", "General", "Costing defaults", "Aluminium systems"]} value={tab} onChange={setTab} />
      {tab === "Company" && <Card title="Company (shown on the PDF)"><div className="grid grid-cols-2 gap-3">
        <Field label="Company name"><input className="inp" value={s.company.name} onChange={(e) => set("company", "name", e.target.value)} /></Field>
        <Field label="Phone"><input className="inp" value={s.company.phone} onChange={(e) => set("company", "phone", e.target.value)} /></Field>
        <Field label="Email"><input className="inp" value={s.company.email} onChange={(e) => set("company", "email", e.target.value)} /></Field>
        <Field label="Logo (PNG or JPG)"><input type="file" accept="image/*" className="inp" onChange={(e) => e.target.files?.[0] && logo(e.target.files[0])} /></Field>
        <Field label="Address" className="col-span-2"><textarea className="inp" rows={2} value={s.company.address} onChange={(e) => set("company", "address", e.target.value)} /></Field>
        {s.company.logo && <img src={`/api/logo?${Date.now()}`} alt="Company logo" className="h-16" />}
      </div><button className="btn btn-primary mt-3" onClick={() => save("company")}>Save company</button></Card>}
      {tab === "General" && <Card title="General"><div className="grid grid-cols-2 gap-3">
        <Field label="Currency"><input className="inp" value={s.general.currency} onChange={(e) => set("general", "currency", e.target.value.toUpperCase())} /></Field>
        <Field label="Default tax %"><Num value={s.general.tax_percent} min={0} max={100} onChange={(v) => set("general", "tax_percent", v || 0)} /></Field>
        <Field label="Quotation number prefix"><input className="inp" value={s.general.quote_prefix} onChange={(e) => set("general", "quote_prefix", e.target.value)} /></Field>
        <Field label="Validity (days)"><Num value={s.general.validity_days} min={1} step={1} onChange={(v) => set("general", "validity_days", v || 30)} /></Field>
        <Field label="Saw blade kerf (mm)"><Num value={s.general.kerf_mm} min={0} onChange={(v) => set("general", "kerf_mm", v || 0)} /></Field>
        <Field label="Aluminium profile charging"><select className="inp" value={s.general.aluminium_charge_mode} onChange={(e) => set("general", "aluminium_charge_mode", e.target.value)}><option value="consumed">Length consumed (+ wastage %)</option><option value="bars">Full bars needed for the batch</option></select></Field>
        <Field label="Board charging"><select className="inp" value={s.general.board_charge_mode} onChange={(e) => set("general", "board_charge_mode", e.target.value)}><option value="sheets">Practical sheets (cutting layout)</option><option value="area">Board area (+ wastage %)</option></select></Field>
        <Field label="Allow rotating pieces on sheets"><select className="inp" value={s.general.allow_rotation ? 1 : 0} onChange={(e) => set("general", "allow_rotation", e.target.value === "1")}><option value={1}>Yes</option><option value={0}>No (grain direction)</option></select></Field>
        <Field label="Terms and conditions (default)" className="col-span-2"><textarea className="inp" rows={6} value={s.general.terms} onChange={(e) => set("general", "terms", e.target.value)} /></Field>
      </div><button className="btn btn-primary mt-3" onClick={() => save("general")}>Save general settings</button></Card>}
      {tab === "Costing defaults" && <div className="grid gap-4 md:grid-cols-2">
        <Card title="Aluminium defaults"><CostEditor cost={s.cost_aluminium} onChange={(c) => setS({ ...s, cost_aluminium: c })} /><button className="btn btn-primary mt-3" onClick={() => save("cost_aluminium")}>Save</button></Card>
        <Card title="Board furniture defaults"><CostEditor cost={s.cost_board} onChange={(c) => setS({ ...s, cost_board: c })} /><button className="btn btn-primary mt-3" onClick={() => save("cost_board")}>Save</button></Card>
        <p className="col-span-2 text-mute">These are starting values. Each designer lets you override them per product.</p>
      </div>}
      {tab === "Aluminium systems" && <Card title="Profile-cutting formulas">
        <p className="mb-3 text-mute">Every window system has its own cutting rules. Edit the formulas to match your supplier's catalogue. Variables: W, H, panels, sliding, fixed, casement, rows, transoms, glass_thk, frame, mullion, glass_perimeter, plus your own “constants”. Saving checks that every formula is valid.</p>
        <div className="mb-2 flex gap-2"><select className="inp w-auto" value={sid ?? ""} onChange={(e) => { const x = systems.find((y) => y.id === +e.target.value); setSid(x.id); setJson(JSON.stringify(x.config, null, 2)); }}>{systems.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
          {sys && <label className="flex items-center gap-1"><input type="checkbox" checked={sys.active} onChange={(e) => setSystems(systems.map((x) => x.id === sid ? { ...x, active: e.target.checked } : x))} /> Active</label>}</div>
        <textarea className="inp h-96 font-mono text-[12px]" spellCheck={false} value={json} onChange={(e) => setJson(e.target.value)} aria-label="System configuration JSON" />
        <button className="btn btn-primary mt-3" onClick={saveSystem}>Save system</button>
      </Card>}
    </div>
  );
}
