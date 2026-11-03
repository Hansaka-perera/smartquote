import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, toast } from "../api";
import { Empty } from "../components/ui";

export default function Products() {
  const nav = useNavigate();
  const [rows, setRows] = useState<any[]>([]);
  const load = () => api("/api/products").then(setRows);
  useEffect(() => { load(); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Products</h1>
      <p className="text-mute">Saved designs. Open one to continue editing it, or use it as a reusable starting point. Save designs from either designer with “Save design”.</p>
      {rows.length === 0 ? <Empty>No saved designs yet.</Empty> : (
        <div className="card overflow-auto"><table className="w-full"><thead><tr><th className="th">Name</th><th className="th">Type</th><th className="th">Size</th><th className="th">Updated</th><th className="th"></th></tr></thead>
          <tbody>{rows.map((p) => <tr key={p.id}><td className="td font-medium">{p.name}</td><td className="td">{p.kind === "aluminium" ? `Aluminium · ${p.system_code}` : "Board furniture"}</td>
            <td className="td">{p.kind === "aluminium" ? `${p.params.width} × ${p.params.height} ${p.params.unit}` : `${p.params.overall?.W} × ${p.params.overall?.H} × ${p.params.overall?.D} ${p.params.unit}`}</td><td className="td">{p.updated_at.slice(0, 10)}</td>
            <td className="td whitespace-nowrap"><button className="btn btn-sm" onClick={() => nav(p.kind === "aluminium" ? "/aluminium" : "/board", { state: { product: p } })}>Open in designer</button> <button className="btn btn-sm btn-danger" onClick={async () => { if (confirm(`Delete ${p.name}?`)) { await api(`/api/products/${p.id}`, { method: "DELETE" }); toast("Deleted"); load(); } }}>Delete</button></td></tr>)}</tbody></table></div>
      )}
    </div>
  );
}
