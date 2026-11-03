import { useState } from "react";
import { fmt } from "../lib/format";

const PAL = ["#5f8fb0", "#7fae8c", "#c79c5b", "#a487b8", "#c27a7a", "#6fb0b5"];

export function BarsView({ plans }: { plans: Record<string, any> }) {
  const codes = Object.keys(plans);
  if (!codes.length) return null;
  return (
    <div className="space-y-4">
      {codes.map((code) => {
        const p = plans[code];
        const labels: string[] = Array.from(new Set(p.bars.flatMap((b: any) => b.cuts.map((c: any) => c.label))));
        return (
          <div key={code}>
            <div className="mb-1 flex flex-wrap items-baseline gap-x-4">
              <b className="font-mono">{code}</b>
              <span>{p.bars_needed} × {fmt(p.stock_length, 0)} mm bar{p.bars_needed > 1 ? "s" : ""}</span>
              <span className="text-mute">waste {fmt(p.waste_pct, 1)}% · usable offcuts {fmt(p.remaining_offcuts_mm / 1000, 2)} m · kerf {p.kerf} mm</span>
            </div>
            <div className="space-y-1">
              {p.bars.map((b: any) => {
                let x = 0;
                return (
                  <svg key={b.index} viewBox="0 0 1000 24" className="block w-full" role="img" aria-label={`Bar ${b.index}`}>
                    <rect width="1000" height="24" fill="var(--sunk)" stroke="var(--line)" />
                    {b.cuts.map((c: any, i: number) => {
                      const w = ((c.length + p.allowance) / p.stock_length) * 1000, x0 = x;
                      x += w + (p.kerf / p.stock_length) * 1000;
                      return (
                        <g key={i}>
                          <rect x={x0} width={w} height="24" fill={PAL[labels.indexOf(c.label) % PAL.length]} stroke="var(--panel)" />
                          {w > 60 && <text x={x0 + w / 2} y="16" fontSize="11" textAnchor="middle" fill="#fff">{fmt(c.length, 0)}</text>}
                        </g>
                      );
                    })}
                    <text x="996" y="16" fontSize="10" textAnchor="end" fill="var(--mute)">{b.offcut_mm > 150 ? `offcut ${fmt(b.offcut_mm, 0)}` : ""}</text>
                  </svg>
                );
              })}
            </div>
            <div className="mt-1 flex flex-wrap gap-3 text-[12px] text-mute">
              {labels.map((l, i) => <span key={l}><i className="mr-1 inline-block h-2 w-2" style={{ background: PAL[i % PAL.length] }} />{l}</span>)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function SheetsView({ sheets }: { sheets: Record<string, any> }) {
  const codes = Object.keys(sheets);
  const [code, setCode] = useState(codes[0]);
  const [idx, setIdx] = useState(0);
  if (!codes.length) return null;
  const s = sheets[codes.includes(code) ? code : codes[0]];
  const L = s.layout, sh = L.sheets[Math.min(idx, L.sheets.length - 1)];
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <select className="inp w-auto" value={code} onChange={(e) => { setCode(e.target.value); setIdx(0); }}>
          {codes.map((c) => <option key={c}>{c}</option>)}
        </select>
        <span>{L.sheets_needed} sheet(s) · {fmt(L.utilisation_pct, 1)}% used</span>
        <div className="flex gap-1">
          {L.sheets.map((x: any, i: number) => <button key={i} className={`btn btn-sm ${i === idx ? "btn-primary" : ""}`} onClick={() => setIdx(i)}>Sheet {i + 1}</button>)}
        </div>
      </div>
      <svg viewBox={`-10 -10 ${L.sheet_length + 20} ${L.sheet_width + 20}`} className="block w-full rounded border border-line bg-sunk" role="img" aria-label="Sheet cutting layout">
        <rect width={L.sheet_length} height={L.sheet_width} fill="#efe6d6" stroke="#5c4a33" strokeWidth="4" />
        {sh.placements.map((p: any, i: number) => (
          <g key={i}>
            <rect x={p.x} y={p.y} width={p.w} height={p.h} fill={PAL[i % PAL.length]} fillOpacity="0.75" stroke="#2b3440" strokeWidth="3" />
            {p.w > 140 && p.h > 70 && (
              <text x={p.x + p.w / 2} y={p.y + p.h / 2} textAnchor="middle" fontSize={Math.min(46, p.h / 3)} fill="#10151b">
                <tspan x={p.x + p.w / 2}>{p.label}</tspan><tspan x={p.x + p.w / 2} dy="1.2em">{Math.round(p.w)}×{Math.round(p.h)}</tspan>
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
