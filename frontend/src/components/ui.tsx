import { ReactNode, useEffect, useState } from "react";
import { onToast } from "../api";

export function Card({ title, actions, children, className = "" }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between border-b border-line px-3 py-2">
          <h2 className="font-semibold">{title}</h2>
          <div className="flex gap-2">{actions}</div>
        </header>
      )}
      <div className="p-3">{children}</div>
    </section>
  );
}

export function Field({ label, children, className = "" }: { label: string; children: ReactNode; className?: string }) {
  return (
    <label className={`block ${className}`}>
      <span className="label">{label}</span>
      {children}
    </label>
  );
}

export function Num({ value, onChange, min, max, step = "any", className = "" }: { value: number; onChange: (v: number) => void; min?: number; max?: number; step?: number | string; className?: string }) {
  return (
    <input type="number" className={`inp ${className}`} value={Number.isFinite(value) ? value : ""} min={min} max={max} step={step}
      onChange={(e) => onChange(e.target.value === "" ? NaN : parseFloat(e.target.value))} />
  );
}

export function Modal({ title, onClose, children, wide }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-auto bg-black/40 p-6" onMouseDown={onClose}>
      <div role="dialog" aria-label={title} className={`card w-full ${wide ? "max-w-5xl" : "max-w-2xl"}`} onMouseDown={(e) => e.stopPropagation()}>
        <header className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
          <button className="btn btn-sm" onClick={onClose} aria-label="Close">Close</button>
        </header>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

export function Toasts() {
  const [m, setM] = useState<{ text: string; kind: string } | null>(null);
  useEffect(() => {
    onToast((x) => { setM(x); setTimeout(() => setM(null), 4500); });
  }, []);
  if (!m) return null;
  return (
    <div role="status" className={`fixed bottom-4 right-4 z-50 max-w-md rounded border px-4 py-2 shadow ${m.kind === "err" ? "border-bad text-bad" : "border-ok text-ok"} bg-panel`}>
      {m.text}
    </div>
  );
}

export function Status({ s }: { s: string }) {
  const c: any = { Approved: "text-ok", Rejected: "text-bad", Expired: "text-bad", Sent: "text-accent", Pending: "text-warn", Draft: "text-mute" };
  return <span className={`font-medium ${c[s] || ""}`}>{s}</span>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="rounded border border-dashed border-line p-6 text-center text-mute">{children}</p>;
}

export function Tabs({ tabs, value, onChange }: { tabs: string[]; value: string; onChange: (t: string) => void }) {
  return (
    <div role="tablist" className="flex gap-1 border-b border-line">
      {tabs.map((t) => (
        <button key={t} role="tab" aria-selected={t === value} onClick={() => onChange(t)}
          className={`px-3 py-1.5 ${t === value ? "border-b-2 border-accent font-semibold text-accent" : "text-mute hover:text-ink"}`}>{t}</button>
      ))}
    </div>
  );
}
