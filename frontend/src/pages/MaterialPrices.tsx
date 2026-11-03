import { useEffect, useState } from "react";
import { api, toast } from "../api";
import { Empty, Modal, Num } from "../components/ui";
import { fmt } from "../lib/format";

export default function MaterialPrices() {
  const [rows, setRows] = useState<any[]>([]);
  const [edits, setEdits] = useState<Record<number, { purchase_price: number; selling_price: number }>>({});
  const [q, setQ] = useState("");
  const [hist, setHist] = useState<any>(null);
  const load = () => api("/api/materials").then((r) => { setRows(r); setEdits({}); });
  useEffect(() => { load(); }, []);
  const val = (m: any, k: "purchase_price" | "selling_price") => edits[m.id]?.[k] ?? m[k];
  const change = (m: any, k: string, v: number) => setEdits({ ...edits, [m.id]: { purchase_price: val(m, "purchase_price"), selling_price: val(m, "selling_price"), [k]: v } as any });
  const dirty = Object.keys(edits).length;
  const save = async () => {
    try {
      const body = Object.entries(edits).map(([id, v]) => ({ id: +id, purchase_price: v.purchase_price || 0, selling_price: v.selling_price || 0 }));
      const r = await api("/api/materials/prices", { body });
      toast(`${r.updated} price(s) updated. Existing quotations were not changed.`); load();
    } catch (e: any) { toast(e.message, "err"); }
  };
  const view = rows.filter((m) => !q || (m.code + m.name).toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2"><h1 className="mr-auto text-xl font-semibold">Material Prices</h1><input className="inp max-w-xs" placeholder="Search" value={q} onChange={(e) => setQ(e.target.value)} /><button className="btn btn-primary" disabled={!dirty} onClick={save}>Save {dirty || ""} change{dirty === 1 ? "" : "s"}</button></div>
      <p className="text-mute">Edit prices directly in the table. Every change is kept in the price history. Quotations already created keep the prices they were calculated with.</p>
      {rows.length === 0 ? <Empty>No materials yet.</Empty> : (
        <div className="card overflow-auto"><table className="w-full">
          <thead><tr><th className="th">Code</th><th className="th">Material</th><th className="th">Unit</th><th className="th">Supplier</th><th className="th num w-40">Purchase price</th><th className="th num w-40">Selling price</th><th className="th"></th></tr></thead>
          <tbody>{view.map((m) => <tr key={m.id} className={edits[m.id] ? "bg-sunk" : ""}><td className="td font-mono">{m.code}</td><td className="td">{m.name}</td><td className="td">{m.unit}</td><td className="td">{m.supplier}</td>
            <td className="td"><Num value={val(m, "purchase_price")} min={0} onChange={(v) => change(m, "purchase_price", v)} /></td>
            <td className="td"><Num value={val(m, "selling_price")} min={0} onChange={(v) => change(m, "selling_price", v)} /></td>
            <td className="td"><button className="btn btn-sm" onClick={async () => setHist({ m, rows: await api(`/api/materials/${m.id}/prices`) })}>History</button></td></tr>)}</tbody>
        </table></div>
      )}
      {hist && <Modal title={`Price history — ${hist.m.code}`} onClose={() => setHist(null)}><table className="w-full"><thead><tr><th className="th">Date</th><th className="th num">Purchase</th><th className="th num">Selling</th><th className="th">Note</th></tr></thead><tbody>{hist.rows.map((r: any, i: number) => <tr key={i}><td className="td">{r.effective_at.slice(0, 16).replace("T", " ")}</td><td className="td num">{fmt(r.purchase_price)}</td><td className="td num">{fmt(r.selling_price)}</td><td className="td">{r.note}</td></tr>)}</tbody></table></Modal>}
    </div>
  );
}
