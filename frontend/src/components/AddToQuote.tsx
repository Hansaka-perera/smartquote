import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, toast } from "../api";
import { Field, Modal, Num } from "./ui";

export default function AddToQuote({ build, defaultName, quantity, disabled }: { build: () => any; defaultName: string; quantity: number; disabled?: boolean }) {
  const [open, setOpen] = useState(false);
  const [qs, setQs] = useState<any[]>([]);
  const [qid, setQid] = useState<number | "">("");
  const [name, setName] = useState(defaultName);
  const [done, setDone] = useState<any>(null);
  useEffect(() => {
    if (open) {
      setName(defaultName); setDone(null);
      api("/api/quotations").then((r) => { const o = r.filter((x: any) => !["Approved", "Rejected", "Expired"].includes(x.status)); setQs(o); setQid(o[0]?.id ?? ""); });
    }
  }, [open]);
  const submit = async () => {
    try {
      const b = build();
      const r = await api(`/api/quotations/${qid}/items`, { body: { ...b, name, quantity } });
      setDone(r); toast("Added to quotation " + r.number);
    } catch (e: any) { toast(e.message, "err"); }
  };
  return (
    <>
      <button className="btn btn-primary" disabled={disabled} onClick={() => setOpen(true)}>Add to quotation</button>
      {open && (
        <Modal title="Add to quotation" onClose={() => setOpen(false)}>
          {done ? (
            <div className="space-y-3">
              <p>Added to <b>{done.number}</b>. The price is now frozen in the quotation; later material price changes will not alter it.</p>
              <div className="flex gap-2"><Link className="btn btn-primary" to={`/quotations/${done.id}`}>Open quotation</Link><button className="btn" onClick={() => setOpen(false)}>Keep designing</button></div>
            </div>
          ) : (
            <div className="space-y-3">
              {qs.length === 0 ? (
                <p>There is no open quotation yet. <Link className="text-accent underline" to="/quotations/new">Create a quotation</Link> first, then come back.</p>
              ) : (
                <Field label="Quotation">
                  <select className="inp" value={qid} onChange={(e) => setQid(Number(e.target.value))}>
                    {qs.map((q) => <option key={q.id} value={q.id}>{q.number} — {q.customer_name} ({q.status})</option>)}
                  </select>
                </Field>
              )}
              <Field label="Item name on quotation"><input className="inp" value={name} onChange={(e) => setName(e.target.value)} /></Field>
              <p className="text-mute">Quantity: <b className="text-ink">{quantity}</b> identical unit(s) (set in the designer).</p>
              <button className="btn btn-primary" disabled={!qid || !name.trim()} onClick={submit}>Add item</button>
            </div>
          )}
        </Modal>
      )}
    </>
  );
}
