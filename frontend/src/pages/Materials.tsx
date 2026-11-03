import { useEffect, useState } from "react";
import { api, toast } from "../api";
import { Card, Empty, Field, Modal, Num } from "../components/ui";
import { fmt } from "../lib/format";

const blank = { code: "", name: "", category: "Hardware", unit: "pcs", purchase_price: 0, selling_price: 0, supplier: "", wastage_pct: 0, min_stock: null, active: true, profile_type: "", bar_length_mm: null, cutting_allowance_mm: null, weight_per_m: null, sheet_length_mm: null, sheet_width_mm: null, thickness_mm: null };

export default function Materials() {
  const [rows, setRows] = useState<any[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [cat, setCat] = useState("");
  const [q, setQ] = useState("");
  const [edit, setEdit] = useState<any>(null);
  const load = () => api("/api/materials").then(setRows);
  useEffect(() => { load(); api("/api/categories").then(setCats); }, []);
  const view = rows.filter((m) => (!cat || m.category === cat) && (!q || (m.code + m.name).toLowerCase().includes(q.toLowerCase())));
  const isAlu = edit?.category === "Aluminium profiles";
  const isBoard = ["MDF boards", "Plywood"].includes(edit?.category);
  const clean = (m: any) => { const o: any = { ...m }; Object.keys(o).forEach((k) => (o[k] === "" || Number.isNaN(o[k])) && (o[k] = null)); o.wastage_pct = o.wastage_pct || 0; o.purchase_price = o.purchase_price || 0; o.selling_price = o.selling_price || 0; return o; };
  const save = async () => {
    try {
      const body = clean(edit);
      if (edit.id) await api(`/api/materials/${edit.id}`, { method: "PUT", body }); else await api("/api/materials", { body });
      toast("Material saved"); setEdit(null); load(); api("/api/categories").then(setCats);
    } catch (e: any) { toast(e.message, "err"); }
  };
  const del = async (m: any) => { if (!confirm(`Delete ${m.code}? Existing quotations keep their frozen prices.`)) return; try { await api(`/api/materials/${m.id}`, { method: "DELETE" }); toast("Deleted"); load(); } catch (e: any) { toast(e.message, "err"); } };
  const set = (k: string, v: any) => setEdit({ ...edit, [k]: v });
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Materials</h1><button className="btn btn-primary" onClick={() => setEdit({ ...blank })}>Add material</button></div>
      <div className="flex gap-2"><input className="inp max-w-xs" placeholder="Search code or name" value={q} onChange={(e) => setQ(e.target.value)} /><select className="inp w-auto" value={cat} onChange={(e) => setCat(e.target.value)}><option value="">All categories</option>{cats.map((c) => <option key={c}>{c}</option>)}</select></div>
      {view.length === 0 ? <Empty>No materials. Add one, or run “python -m app.seed” to load sample test data.</Empty> : (
        <div className="card overflow-auto"><table className="w-full text-[13px]">
          <thead><tr>{["Code", "Name", "Category", "Unit", "Purchase", "Selling", "Supplier", "Wastage %", "Size", "Active", ""].map((t, i) => <th key={i} className={`th ${[4, 5, 7].includes(i) ? "num" : ""}`}>{t}</th>)}</tr></thead>
          <tbody>{view.map((m) => <tr key={m.id} className={m.active ? "" : "text-mute"}><td className="td font-mono">{m.code}</td><td className="td">{m.name}</td><td className="td">{m.category}</td><td className="td">{m.unit}</td><td className="td num">{fmt(m.purchase_price)}</td><td className="td num">{fmt(m.selling_price)}</td><td className="td">{m.supplier}</td><td className="td num">{m.wastage_pct}</td>
            <td className="td">{m.bar_length_mm ? `bar ${m.bar_length_mm} mm` : m.sheet_length_mm ? `${m.sheet_length_mm}×${m.sheet_width_mm}×${m.thickness_mm}` : ""}</td><td className="td">{m.active ? "Yes" : "No"}</td>
            <td className="td whitespace-nowrap"><button className="btn btn-sm" onClick={() => setEdit({ ...m, supplier: m.supplier ?? "" })}>Edit</button> <button className="btn btn-sm btn-danger" onClick={() => del(m)}>Delete</button></td></tr>)}</tbody>
        </table></div>
      )}
      {edit && (
        <Modal title={edit.id ? `Edit ${edit.code}` : "Add material"} onClose={() => setEdit(null)}>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Material code *"><input className="inp" value={edit.code} onChange={(e) => set("code", e.target.value)} /></Field>
            <Field label="Name *"><input className="inp" value={edit.name} onChange={(e) => set("name", e.target.value)} /></Field>
            <Field label="Category"><input className="inp" list="cats" value={edit.category} onChange={(e) => set("category", e.target.value)} /><datalist id="cats">{cats.map((c) => <option key={c} value={c} />)}</datalist></Field>
            <Field label="Unit (m, m2, pcs, sheet…)"><input className="inp" value={edit.unit} onChange={(e) => set("unit", e.target.value)} /></Field>
            <Field label="Purchase price"><Num value={edit.purchase_price} min={0} onChange={(v) => set("purchase_price", v)} /></Field>
            <Field label="Selling price"><Num value={edit.selling_price} min={0} onChange={(v) => set("selling_price", v)} /></Field>
            <Field label="Supplier"><input className="inp" value={edit.supplier} onChange={(e) => set("supplier", e.target.value)} /></Field>
            <Field label="Wastage %"><Num value={edit.wastage_pct} min={0} max={100} onChange={(v) => set("wastage_pct", v)} /></Field>
            <Field label="Minimum stock (optional)"><Num value={edit.min_stock ?? NaN} min={0} onChange={(v) => set("min_stock", v)} /></Field>
            <Field label="Status"><select className="inp" value={edit.active ? 1 : 0} onChange={(e) => set("active", e.target.value === "1")}><option value={1}>Active</option><option value={0}>Inactive</option></select></Field>
            {isAlu && (<>
              <Field label="Profile type"><input className="inp" value={edit.profile_type ?? ""} onChange={(e) => set("profile_type", e.target.value)} /></Field>
              <Field label="Standard bar length (mm)"><Num value={edit.bar_length_mm ?? NaN} min={1} onChange={(v) => set("bar_length_mm", v)} /></Field>
              <Field label="Cutting allowance (mm per piece)"><Num value={edit.cutting_allowance_mm ?? NaN} min={0} onChange={(v) => set("cutting_allowance_mm", v)} /></Field>
              <Field label="Weight per metre (kg, optional)"><Num value={edit.weight_per_m ?? NaN} min={0} onChange={(v) => set("weight_per_m", v)} /></Field>
            </>)}
            {isBoard && (<>
              <Field label="Sheet length (mm) — 8 ft = 2440"><Num value={edit.sheet_length_mm ?? NaN} min={1} onChange={(v) => set("sheet_length_mm", v)} /></Field>
              <Field label="Sheet width (mm) — 4 ft = 1220"><Num value={edit.sheet_width_mm ?? NaN} min={1} onChange={(v) => set("sheet_width_mm", v)} /></Field>
              <Field label="Thickness (mm)"><Num value={edit.thickness_mm ?? NaN} min={1} onChange={(v) => set("thickness_mm", v)} /></Field>
              <p className="col-span-2 text-[12px] text-mute">Use unit “sheet” so the price is per full sheet and the cutting-layout optimiser is used.</p>
            </>)}
          </div>
          <div className="mt-4 flex gap-2"><button className="btn btn-primary" disabled={!edit.code || !edit.name} onClick={save}>Save material</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></div>
        </Modal>
      )}
    </div>
  );
}
