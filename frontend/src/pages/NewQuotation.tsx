import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, toast } from "../api";
import { Card, Field, Num } from "../components/ui";
import { today } from "../lib/format";

export default function NewQuotation() {
  const nav = useNavigate();
  const [customers, setCustomers] = useState<any[]>([]);
  const [f, setF] = useState<any>({ customer_id: "", customer_name: "", company: "", address: "", phone: "", email: "", project_name: "", delivery_location: "", notes: "", quote_date: today(), expiry_date: "", discount_mode: "percent", discount_value: 0, tax_percent: null });
  useEffect(() => { api("/api/customers").then(setCustomers); api("/api/settings").then((s) => setF((x: any) => ({ ...x, tax_percent: s.general.tax_percent }))); }, []);
  const pick = (id: string) => {
    const c = customers.find((x) => String(x.id) === id);
    setF({ ...f, customer_id: id, ...(c ? { customer_name: c.name, company: c.company ?? "", address: c.address ?? "", phone: c.phone ?? "", email: c.email ?? "" } : {}) });
  };
  const set = (k: string, v: any) => setF({ ...f, [k]: v });
  const create = async () => {
    try {
      const body: any = { ...f, customer_id: f.customer_id ? Number(f.customer_id) : null };
      if (!body.expiry_date) delete body.expiry_date;
      Object.keys(body).forEach((k) => (body[k] === "" || body[k] === null) && delete body[k]);
      const q = await api("/api/quotations", { body });
      toast(`Quotation ${q.number} created`);
      nav(`/quotations/${q.id}`);
    } catch (e: any) { toast(e.message, "err"); }
  };
  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-xl font-semibold">New quotation</h1>
      <Card title="Customer">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Existing customer" className="md:col-span-2"><select className="inp" value={f.customer_id} onChange={(e) => pick(e.target.value)}><option value="">— type a new customer below —</option>{customers.map((c) => <option key={c.id} value={c.id}>{c.name}{c.company ? ` (${c.company})` : ""}</option>)}</select></Field>
          <Field label="Customer name *"><input className="inp" value={f.customer_name} onChange={(e) => set("customer_name", e.target.value)} /></Field>
          <Field label="Company"><input className="inp" value={f.company} onChange={(e) => set("company", e.target.value)} /></Field>
          <Field label="Phone"><input className="inp" value={f.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
          <Field label="Email"><input className="inp" type="email" value={f.email} onChange={(e) => set("email", e.target.value)} /></Field>
          <Field label="Address" className="md:col-span-2"><textarea className="inp" rows={2} value={f.address} onChange={(e) => set("address", e.target.value)} /></Field>
        </div>
      </Card>
      <Card title="Project">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Project name"><input className="inp" value={f.project_name} onChange={(e) => set("project_name", e.target.value)} /></Field>
          <Field label="Delivery location"><input className="inp" value={f.delivery_location} onChange={(e) => set("delivery_location", e.target.value)} /></Field>
          <Field label="Date"><input className="inp" type="date" value={f.quote_date} onChange={(e) => set("quote_date", e.target.value)} /></Field>
          <Field label="Expiry date (blank = default validity)"><input className="inp" type="date" value={f.expiry_date} onChange={(e) => set("expiry_date", e.target.value)} /></Field>
          <Field label="Discount type"><select className="inp" value={f.discount_mode} onChange={(e) => set("discount_mode", e.target.value)}><option value="percent">Percentage</option><option value="fixed">Fixed amount</option></select></Field>
          <Field label="Discount"><Num value={f.discount_value} min={0} onChange={(v) => set("discount_value", v || 0)} /></Field>
          <Field label="Tax %"><Num value={f.tax_percent ?? 0} min={0} max={100} onChange={(v) => set("tax_percent", v || 0)} /></Field>
          <Field label="Notes" className="md:col-span-2"><textarea className="inp" rows={2} value={f.notes} onChange={(e) => set("notes", e.target.value)} /></Field>
        </div>
      </Card>
      <button className="btn btn-primary" disabled={!f.customer_name.trim()} onClick={create}>Create quotation</button>
      <p className="text-mute">After creating it, design items in the Aluminium or Board designer and use “Add to quotation”.</p>
    </div>
  );
}
