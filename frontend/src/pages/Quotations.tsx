import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, toast } from "../api";
import { Card, Empty, Field, Modal, Num, Status } from "../components/ui";
import { CostSummary } from "../components/Cost";
import { fmt, money } from "../lib/format";

const STATUSES = ["Draft", "Sent", "Pending", "Approved", "Rejected", "Expired"];

export function QuotationList() {
  const [rows, setRows] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [f, setF] = useState<any>({ q: "", status: "", customer_id: "", date_from: "", date_to: "" });
  useEffect(() => { api("/api/customers").then(setCustomers); }, []);
  useEffect(() => {
    const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as any).toString();
    api(`/api/quotations?${p}`).then(setRows);
  }, [JSON.stringify(f)]);
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Quotations</h1><Link className="btn btn-primary" to="/quotations/new">New quotation</Link></div>
      <Card>
        <div className="grid gap-2 md:grid-cols-5">
          <Field label="Search"><input className="inp" placeholder="Number, customer, project" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} /></Field>
          <Field label="Status"><select className="inp" value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })}><option value="">All</option>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select></Field>
          <Field label="Customer"><select className="inp" value={f.customer_id} onChange={(e) => setF({ ...f, customer_id: e.target.value })}><option value="">All</option>{customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
          <Field label="From"><input type="date" className="inp" value={f.date_from} onChange={(e) => setF({ ...f, date_from: e.target.value })} /></Field>
          <Field label="To"><input type="date" className="inp" value={f.date_to} onChange={(e) => setF({ ...f, date_to: e.target.value })} /></Field>
        </div>
      </Card>
      {rows.length === 0 ? <Empty>No quotations match.</Empty> : (
        <div className="card overflow-auto"><table className="w-full">
          <thead><tr><th className="th">Number</th><th className="th">Date</th><th className="th">Customer</th><th className="th">Project</th><th className="th num">Items</th><th className="th">Status</th><th className="th num">Total</th></tr></thead>
          <tbody>{rows.map((q) => <tr key={q.id}><td className="td"><Link className="text-accent underline" to={`/quotations/${q.id}`}>{q.number}</Link></td><td className="td">{q.quote_date}</td><td className="td">{q.customer_name}</td><td className="td">{q.project_name}</td><td className="td num">{q.item_count}</td><td className="td"><Status s={q.status} /></td><td className="td num">{money(q.total, q.currency)}</td></tr>)}</tbody>
        </table></div>
      )}
    </div>
  );
}

export function QuotationDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [q, setQ] = useState<any>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [pdf, setPdf] = useState(false);
  const [vers, setVers] = useState<any[] | null>(null);
  const [cmp, setCmp] = useState<any>(null);
  const [pair, setPair] = useState<[number, number]>([1, 1]);
  const [edit, setEdit] = useState<any>(null);
  const load = () => api(`/api/quotations/${id}`).then(setQ).catch((e) => toast(e.message, "err"));
  useEffect(() => { load(); }, [id]);
  if (!q) return <p className="text-mute">Loading…</p>;
  const run = async (fn: () => Promise<any>, ok?: string) => { try { const r = await fn(); if (ok) toast(ok); return r; } catch (e: any) { toast(e.message, "err"); } };
  const saveEdit = async () => { const r = await run(() => api(`/api/quotations/${id}`, { method: "PUT", body: edit }), "Quotation updated"); if (r) { setQ(r); setEdit(null); } };
  const showVersions = async () => { const v = await api(`/api/quotations/${id}/versions`); setVers(v); setPair([v[0]?.version_no, v[v.length - 1]?.version_no]); setCmp(null); };
  const printPdf = () => { const w = window.open(`/api/quotations/${id}/pdf`, "_blank"); w?.addEventListener("load", () => w.print()); };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="mr-auto"><h1 className="text-xl font-semibold">{q.number} <span className="text-base"><Status s={q.status} /></span></h1><div className="text-mute">Version {q.version} · {q.customer_name}{q.project_name ? ` · ${q.project_name}` : ""}</div></div>
        <button className="btn" onClick={() => setPdf(true)}>Preview PDF</button>
        <a className="btn" href={`/api/quotations/${id}/pdf?download=true`}>Download PDF</a>
        <button className="btn" onClick={printPdf}>Print</button>
        <a className="btn" href={`/api/quotations/${id}/xlsx`}>Export Excel</a>
        <button className="btn" onClick={async () => { const n = await run(() => api(`/api/quotations/${id}/duplicate`, { method: "POST" }), "Duplicated"); if (n) nav(`/quotations/${n.id}`); }}>Duplicate</button>
        <button className="btn" onClick={showVersions}>History</button>
        <button className="btn" onClick={() => setEdit({ customer_name: q.customer_name, company: q.company ?? "", address: q.address ?? "", phone: q.phone ?? "", email: q.email ?? "", project_name: q.project_name ?? "", delivery_location: q.delivery_location ?? "", notes: q.notes ?? "", terms: q.terms ?? "", status: q.status, expiry_date: q.expiry_date ?? "", discount_mode: q.discount_mode, discount_value: q.discount_value, tax_percent: q.tax_percent })}>Edit details</button>
        <button className="btn btn-danger" onClick={async () => { if (confirm(`Delete ${q.number}?`)) { await run(() => api(`/api/quotations/${id}`, { method: "DELETE" })); nav("/quotations"); } }}>Delete</button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card title={`Items (${q.items.length})`} actions={<><Link className="btn btn-sm" to="/aluminium">Design aluminium</Link><Link className="btn btn-sm" to="/board">Design furniture</Link></>}>
          {q.items.length === 0 ? <Empty>No items yet. Design a product and choose “Add to quotation”.</Empty> : (
            <table className="w-full"><thead><tr><th className="th">#</th><th className="th">Item</th><th className="th num">Qty</th><th className="th num">Unit price</th><th className="th num">Total</th><th className="th"></th></tr></thead>
              <tbody>{q.items.map((it: any) => (<>
                <tr key={it.id}><td className="td">{it.position}</td>
                  <td className="td"><b>{it.name}</b><div className="text-[12px] text-mute">{it.kind === "aluminium" ? `${it.params.width} × ${it.params.height} ${it.params.unit} · ${it.system_code}` : `W ${it.params.overall?.W} × H ${it.params.overall?.H} × D ${it.params.overall?.D} ${it.params.unit}`} · priced {it.priced_at.slice(0, 10)}</div></td>
                  <td className="td num">{it.quantity}</td><td className="td num">{fmt(it.unit_price)}</td><td className="td num">{fmt(it.total_price)}</td>
                  <td className="td whitespace-nowrap"><button className="btn btn-sm" onClick={() => setOpen(open === it.id ? null : it.id)}>{open === it.id ? "Hide" : "Breakdown"}</button>{" "}
                    <button className="btn btn-sm" title="Recalculate this item with today's material prices" onClick={async () => { if (confirm("Re-price this item using the CURRENT material prices? Its price will change.")) { const r = await run(() => api(`/api/quotations/${id}/items/${it.id}/reprice`, { method: "POST" }), "Item re-priced"); if (r) setQ(r); } }}>Re-price</button>{" "}
                    <button className="btn btn-sm btn-danger" onClick={async () => { if (confirm(`Remove ${it.name}?`)) { const r = await run(() => api(`/api/quotations/${id}/items/${it.id}`, { method: "DELETE" })); if (r) setQ(r); } }}>Remove</button></td></tr>
                {open === it.id && <tr key={`${it.id}b`}><td colSpan={6} className="td bg-sunk"><CostSummary calc={it.calc} currency={q.currency} /><p className="mt-2 text-[12px] text-mute">Frozen price snapshot from {it.priced_at.slice(0, 16).replace("T", " ")} — later material price changes do not affect this quotation.</p></td></tr>}
              </>))}</tbody></table>
          )}
        </Card>
        <Card title="Totals">
          <table className="w-full"><tbody>
            <tr><td className="td">Subtotal</td><td className="td num">{fmt(q.subtotal)}</td></tr>
            <tr><td className="td">Discount {q.discount_mode === "percent" ? `(${q.discount_value}%)` : ""}</td><td className="td num">− {fmt(q.discount_amount)}</td></tr>
            <tr><td className="td">Tax ({q.tax_percent}%)</td><td className="td num">{fmt(q.tax_amount)}</td></tr>
            <tr className="bg-accent text-accent-ink"><td className="px-2 py-2 font-semibold">Grand total</td><td className="px-2 py-2 num font-semibold">{money(q.total, q.currency)}</td></tr>
          </tbody></table>
          <p className="mt-2 text-[12px] text-mute">Date {q.quote_date} · valid until {q.expiry_date}</p>
        </Card>
      </div>

      {pdf && <Modal wide title={`Preview — ${q.number}`} onClose={() => setPdf(false)}><iframe title="Quotation PDF" src={`/api/quotations/${id}/pdf`} className="h-[75vh] w-full rounded border border-line" /></Modal>}

      {edit && (
        <Modal title="Edit quotation details" onClose={() => setEdit(null)}>
          <div className="grid gap-3 md:grid-cols-2">
            {([["customer_name", "Customer name"], ["company", "Company"], ["phone", "Phone"], ["email", "Email"], ["project_name", "Project"], ["delivery_location", "Delivery location"]] as const).map(([k, l]) => <Field key={k} label={l}><input className="inp" value={edit[k]} onChange={(e) => setEdit({ ...edit, [k]: e.target.value })} /></Field>)}
            <Field label="Status"><select className="inp" value={edit.status} onChange={(e) => setEdit({ ...edit, status: e.target.value })}>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select></Field>
            <Field label="Expiry date"><input className="inp" type="date" value={edit.expiry_date} onChange={(e) => setEdit({ ...edit, expiry_date: e.target.value })} /></Field>
            <Field label="Discount type"><select className="inp" value={edit.discount_mode} onChange={(e) => setEdit({ ...edit, discount_mode: e.target.value })}><option value="percent">Percentage</option><option value="fixed">Fixed amount</option></select></Field>
            <Field label="Discount"><Num value={edit.discount_value} min={0} onChange={(v) => setEdit({ ...edit, discount_value: v || 0 })} /></Field>
            <Field label="Tax %"><Num value={edit.tax_percent} min={0} max={100} onChange={(v) => setEdit({ ...edit, tax_percent: v || 0 })} /></Field>
            <Field label="Address" className="md:col-span-2"><textarea className="inp" rows={2} value={edit.address} onChange={(e) => setEdit({ ...edit, address: e.target.value })} /></Field>
            <Field label="Notes" className="md:col-span-2"><textarea className="inp" rows={2} value={edit.notes} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} /></Field>
            <Field label="Terms and conditions" className="md:col-span-2"><textarea className="inp" rows={5} value={edit.terms} onChange={(e) => setEdit({ ...edit, terms: e.target.value })} /></Field>
          </div>
          <div className="mt-4 flex gap-2"><button className="btn btn-primary" onClick={saveEdit}>Save changes</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></div>
        </Modal>
      )}

      {vers && (
        <Modal wide title="Quotation history" onClose={() => setVers(null)}>
          <table className="w-full"><thead><tr><th className="th">Version</th><th className="th">When</th><th className="th">Change</th><th className="th">Status</th><th className="th num">Total</th></tr></thead>
            <tbody>{vers.map((v) => <tr key={v.version_no}><td className="td">v{v.version_no}</td><td className="td">{v.created_at.slice(0, 16).replace("T", " ")}</td><td className="td">{v.note}</td><td className="td">{v.status}</td><td className="td num">{fmt(v.total)}</td></tr>)}</tbody></table>
          <div className="mt-4 flex flex-wrap items-end gap-2">
            <Field label="Compare"><select className="inp" value={pair[0]} onChange={(e) => setPair([+e.target.value, pair[1]])}>{vers.map((v) => <option key={v.version_no} value={v.version_no}>v{v.version_no}</option>)}</select></Field>
            <Field label="with"><select className="inp" value={pair[1]} onChange={(e) => setPair([pair[0], +e.target.value])}>{vers.map((v) => <option key={v.version_no} value={v.version_no}>v{v.version_no}</option>)}</select></Field>
            <button className="btn btn-primary" onClick={async () => setCmp(await run(() => api(`/api/quotations/${id}/versions/compare?a=${pair[0]}&b=${pair[1]}`)))}>Compare</button>
          </div>
          {cmp && (<div className="mt-3 grid gap-4 md:grid-cols-2">
            <div><h3 className="mb-1 font-semibold">Header and totals</h3>{cmp.fields.length === 0 ? <p className="text-mute">No differences.</p> : <table className="w-full"><tbody>{cmp.fields.map((x: any) => <tr key={x.field}><td className="td">{x.field}</td><td className="td">{String(x.from)}</td><td className="td">→ {String(x.to)}</td></tr>)}</tbody></table>}</div>
            <div><h3 className="mb-1 font-semibold">Items</h3>{cmp.items.length === 0 ? <p className="text-mute">No differences.</p> : <table className="w-full"><tbody>{cmp.items.map((x: any, i: number) => <tr key={i}><td className="td">{x.item}</td><td className="td">{x.change}</td><td className="td num">{x.from != null ? fmt(x.from) : ""} {x.from != null && x.to != null ? "→" : ""} {x.to != null ? fmt(x.to) : ""}</td></tr>)}</tbody></table>}</div>
          </div>)}
        </Modal>
      )}
    </div>
  );
}
