import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Card, Empty, Status } from "../components/ui";
import { money } from "../lib/format";

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api("/api/dashboard").then(setD).catch(() => setD(false)); }, []);
  if (d === false) return <Empty>Cannot reach the SmartQuote server. Start it with start.bat and refresh.</Empty>;
  if (!d) return <p className="text-mute">Loading…</p>;
  const stat = (label: string, v: string | number, sub?: string) => (
    <div className="card p-3"><div className="text-[12px] text-mute">{label}</div><div className="text-2xl font-semibold">{v}</div>{sub && <div className="text-[12px] text-mute">{sub}</div>}</div>
  );
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Dashboard</h1><Link className="btn btn-primary" to="/quotations/new">New quotation</Link></div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {stat("Total quotations", d.total_quotations)}
        {stat("Pending (sent / pending)", d.pending_quotations)}
        {stat("Approved", d.approved_quotations, money(d.approved_value, d.currency))}
        {stat("Total quotation value", money(d.total_value, d.currency))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <Card title="Recent quotations" actions={<Link className="btn btn-sm" to="/quotations">All quotations</Link>}>
          {d.recent_quotations.length === 0 ? <Empty>No quotations yet. Design a window or a cupboard and add it to a new quotation.</Empty> : (
            <table className="w-full"><thead><tr><th className="th">Number</th><th className="th">Customer</th><th className="th">Status</th><th className="th num">Total</th></tr></thead>
              <tbody>{d.recent_quotations.map((q: any) => <tr key={q.id}><td className="td"><Link className="text-accent underline" to={`/quotations/${q.id}`}>{q.number}</Link></td><td className="td">{q.customer_name}</td><td className="td"><Status s={q.status} /></td><td className="td num">{money(q.total, q.currency)}</td></tr>)}</tbody></table>
          )}
        </Card>
        <Card title="Recent customers" actions={<Link className="btn btn-sm" to="/customers">All customers</Link>}>
          {d.recent_customers.length === 0 ? <Empty>No customers yet.</Empty> : <ul className="space-y-2">{d.recent_customers.map((c: any) => <li key={c.id}><b>{c.name}</b><div className="text-mute">{c.company}</div></li>)}</ul>}
        </Card>
      </div>
    </div>
  );
}
