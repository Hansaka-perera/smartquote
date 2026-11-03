import { useEffect, useState } from "react";
import { api, toast } from "../api";
import { Empty, Field, Modal } from "../components/ui";

export default function Customers() {
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [edit, setEdit] = useState<any>(null);
  const load = () => api(`/api/customers?q=${encodeURIComponent(q)}`).then(setRows);
  useEffect(() => { load(); }, [q]);
  const save = async () => {
    try { if (edit.id) await api(`/api/customers/${edit.id}`, { method: "PUT", body: edit }); else await api("/api/customers", { body: edit }); toast("Customer saved"); setEdit(null); load(); }
    catch (e: any) { toast(e.message, "err"); }
  };
  const set = (k: string, v: string) => setEdit({ ...edit, [k]: v });
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2"><h1 className="mr-auto text-xl font-semibold">Customers</h1><input className="inp max-w-xs" placeholder="Search" value={q} onChange={(e) => setQ(e.target.value)} /><button className="btn btn-primary" onClick={() => setEdit({ name: "", company: "", address: "", phone: "", email: "" })}>Add customer</button></div>
      {rows.length === 0 ? <Empty>No customers found.</Empty> : (
        <div className="card overflow-auto"><table className="w-full"><thead><tr><th className="th">Name</th><th className="th">Company</th><th className="th">Phone</th><th className="th">Email</th><th className="th">Address</th><th className="th"></th></tr></thead>
          <tbody>{rows.map((c) => <tr key={c.id}><td className="td font-medium">{c.name}</td><td className="td">{c.company}</td><td className="td">{c.phone}</td><td className="td">{c.email}</td><td className="td">{c.address}</td>
            <td className="td whitespace-nowrap"><button className="btn btn-sm" onClick={() => setEdit({ ...c, company: c.company ?? "", address: c.address ?? "", phone: c.phone ?? "", email: c.email ?? "" })}>Edit</button> <button className="btn btn-sm btn-danger" onClick={async () => { if (confirm(`Delete ${c.name}? Their quotations are kept.`)) { await api(`/api/customers/${c.id}`, { method: "DELETE" }); load(); } }}>Delete</button></td></tr>)}</tbody></table></div>
      )}
      {edit && <Modal title={edit.id ? "Edit customer" : "Add customer"} onClose={() => setEdit(null)}>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Name *"><input className="inp" value={edit.name} onChange={(e) => set("name", e.target.value)} /></Field>
          <Field label="Company"><input className="inp" value={edit.company} onChange={(e) => set("company", e.target.value)} /></Field>
          <Field label="Phone"><input className="inp" value={edit.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
          <Field label="Email"><input className="inp" value={edit.email} onChange={(e) => set("email", e.target.value)} /></Field>
          <Field label="Address" className="col-span-2"><textarea className="inp" rows={2} value={edit.address} onChange={(e) => set("address", e.target.value)} /></Field>
        </div>
        <div className="mt-4 flex gap-2"><button className="btn btn-primary" disabled={!edit.name.trim()} onClick={save}>Save customer</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></div>
      </Modal>}
    </div>
  );
}
