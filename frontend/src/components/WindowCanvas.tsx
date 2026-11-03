import { useEffect, useRef, useState } from "react";
import { geometry, Panel } from "../lib/window";

interface Props {
  widthMm: number; heightMm: number; panels: Panel[]; transoms: number; frame: number; mullion: number;
  selected: number | null; onSelect: (i: number | null) => void;
  onResize: (wMm: number, hMm: number) => void; snap: number; grid: boolean; unit: string;
}

export default function WindowCanvas(p: Props) {
  const { widthMm: W, heightMm: H } = p;
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const svgRef = useRef<SVGSVGElement>(null);
  const gRef = useRef<SVGGElement>(null);
  const drag = useRef<null | { kind: "pan" | "w" | "h" | "wh"; sx: number; sy: number; px: number; py: number }>(null);

  const base = Math.min(720 / W, 400 / H);
  const s = base * zoom;
  const ox = 500 - (W * s) / 2 + pan.x, oy = 300 - (H * s) / 2 + pan.y;
  const cells = geometry(W, H, p.panels, p.transoms, p.frame, p.mullion);
  const fs = 13 / s;               // font size in mm units so text stays ~13px
  const sw = 1 / s;                // 1 px stroke

  useEffect(() => {   // wheel zoom needs a non-passive listener
    const el = svgRef.current;
    if (!el) return;
    const h = (e: WheelEvent) => { e.preventDefault(); setZoom((z) => Math.min(6, Math.max(0.25, z * (e.deltaY < 0 ? 1.1 : 1 / 1.1)))); };
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, []);

  const local = (e: React.PointerEvent) => {
    const g = gRef.current!, pt = svgRef.current!.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const r = pt.matrixTransform(g.getScreenCTM()!.inverse());
    return { x: r.x, y: r.y };
  };
  const snapV = (v: number) => (p.snap > 0 ? Math.round(v / p.snap) * p.snap : Math.round(v));
  const start = (kind: "pan" | "w" | "h" | "wh") => (e: React.PointerEvent) => {
    e.stopPropagation();
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    drag.current = { kind, sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y };
  };
  const move = (e: React.PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    if (d.kind === "pan") {
      const k = 1000 / (svgRef.current!.getBoundingClientRect().width || 1000);
      setPan({ x: d.px + (e.clientX - d.sx) * k, y: d.py + (e.clientY - d.sy) * k });
    } else {
      const l = local(e);
      const nw = d.kind !== "h" ? Math.min(12000, Math.max(300, snapV(l.x))) : W;
      const nh = d.kind !== "w" ? Math.min(12000, Math.max(300, snapV(l.y))) : H;
      p.onResize(nw, nh);
    }
  };
  const end = () => { drag.current = null; };
  const hs = 12 / s;

  const unitLabel = (mm: number) => {
    const f: any = { mm: 1, cm: 10, m: 1000, in: 25.4, ft: 304.8 };
    const v = mm / f[p.unit];
    return `${Number.isInteger(v) ? v : v.toFixed(p.unit === "mm" ? 0 : 2)} ${p.unit}`;
  };

  return (
    <div className="relative rounded border border-line bg-sunk">
      <div className="absolute left-2 top-2 z-10 flex gap-1">
        <button className="btn btn-sm" onClick={() => setZoom((z) => Math.min(6, z * 1.2))} aria-label="Zoom in">+</button>
        <button className="btn btn-sm" onClick={() => setZoom((z) => Math.max(0.25, z / 1.2))} aria-label="Zoom out">−</button>
        <button className="btn btn-sm" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>Fit</button>
        <span className="self-center px-1 text-[12px] text-mute">{Math.round(zoom * 100)}%</span>
      </div>
      <svg ref={svgRef} viewBox="0 0 1000 600" className="block h-[440px] w-full touch-none select-none"
        onPointerMove={move} onPointerUp={end} onPointerDown={start("pan")} style={{ cursor: "grab" }}
        onClick={() => p.onSelect(null)}>
        <defs>
          <pattern id="g100" width="100" height="100" patternUnits="userSpaceOnUse">
            <path d="M100 0H0V100" fill="none" stroke="var(--line)" strokeWidth={sw} />
          </pattern>
          <pattern id="g500" width="500" height="500" patternUnits="userSpaceOnUse">
            <path d="M500 0H0V500" fill="none" stroke="var(--mute)" strokeOpacity="0.35" strokeWidth={sw} />
          </pattern>
        </defs>
        <g ref={gRef} transform={`translate(${ox} ${oy}) scale(${s})`}>
          {p.grid && (<>
            <rect x={-3000} y={-3000} width={18000} height={18000} fill="url(#g100)" pointerEvents="none" />
            <rect x={-3000} y={-3000} width={18000} height={18000} fill="url(#g500)" pointerEvents="none" />
          </>)}
          <rect x={0} y={0} width={W} height={H} fill="#8e99a4" stroke="#2b3440" strokeWidth={2 * sw} />
          {cells.map((c, i) => {
            const sel = p.selected === c.col;
            const cx = c.x + c.w / 2, cy = c.y + c.h / 2, dir = c.direction === "right" ? 1 : -1;
            return (
              <g key={i} onClick={(e) => { e.stopPropagation(); p.onSelect(c.col); }} style={{ cursor: "pointer" }}>
                <rect x={c.x} y={c.y} width={c.w} height={c.h} fill="#d8eaf3" stroke={sel ? "var(--accent)" : "#2b3440"} strokeWidth={(sel ? 3.5 : 1) * sw} />
                {c.type === "sliding" && (<>
                  <line x1={cx - dir * c.w * 0.25} y1={cy} x2={cx + dir * c.w * 0.25} y2={cy} stroke="#1d4e6b" strokeWidth={2 * sw} />
                  <polygon points={`${cx + dir * c.w * 0.25},${cy} ${cx + dir * (c.w * 0.25 - 14 / s)},${cy - 6 / s} ${cx + dir * (c.w * 0.25 - 14 / s)},${cy + 6 / s}`} fill="#1d4e6b" />
                </>)}
                {c.type === "casement" && (() => {
                  const hinge = c.direction === "right" ? c.x + c.w : c.x, free = c.direction === "right" ? c.x : c.x + c.w;
                  return (<>
                    <line x1={free} y1={cy} x2={hinge} y2={c.y} stroke="#1d4e6b" strokeWidth={sw} strokeDasharray={`${6 / s} ${4 / s}`} />
                    <line x1={free} y1={cy} x2={hinge} y2={c.y + c.h} stroke="#1d4e6b" strokeWidth={sw} strokeDasharray={`${6 / s} ${4 / s}`} />
                  </>);
                })()}
                {c.type === "fixed" && <text x={cx} y={cy} fontSize={fs} textAnchor="middle" fill="#5a6b78">FIXED</text>}
              </g>
            );
          })}
          {/* dimensions */}
          <g fill="var(--ink)" fontSize={fs} pointerEvents="none">
            <line x1={0} y1={H + 40 / s} x2={W} y2={H + 40 / s} stroke="var(--ink)" strokeWidth={sw} />
            <line x1={0} y1={H + 30 / s} x2={0} y2={H + 50 / s} stroke="var(--ink)" strokeWidth={sw} />
            <line x1={W} y1={H + 30 / s} x2={W} y2={H + 50 / s} stroke="var(--ink)" strokeWidth={sw} />
            <text x={W / 2} y={H + 58 / s} textAnchor="middle">{unitLabel(W)}</text>
            <line x1={-40 / s} y1={0} x2={-40 / s} y2={H} stroke="var(--ink)" strokeWidth={sw} />
            <line x1={-50 / s} y1={0} x2={-30 / s} y2={0} stroke="var(--ink)" strokeWidth={sw} />
            <line x1={-50 / s} y1={H} x2={-30 / s} y2={H} stroke="var(--ink)" strokeWidth={sw} />
            <text transform={`translate(${-52 / s} ${H / 2}) rotate(-90)`} textAnchor="middle">{unitLabel(H)}</text>
            {cells.filter((c) => c.y === p.frame).map((c, i) => (
              <text key={i} x={c.x + c.w / 2} y={-10 / s} textAnchor="middle" fill="var(--mute)">{unitLabel(c.w)}</text>
            ))}
          </g>
          {/* resize handles */}
          <rect x={W - hs / 2} y={H / 2 - hs} width={hs} height={hs * 2} fill="var(--accent)" style={{ cursor: "ew-resize" }} onPointerDown={start("w")} onClick={(e) => e.stopPropagation()}><title>Drag to change width</title></rect>
          <rect x={W / 2 - hs} y={H - hs / 2} width={hs * 2} height={hs} fill="var(--accent)" style={{ cursor: "ns-resize" }} onPointerDown={start("h")} onClick={(e) => e.stopPropagation()}><title>Drag to change height</title></rect>
          <rect x={W - hs / 2} y={H - hs / 2} width={hs} height={hs} fill="var(--accent)" style={{ cursor: "nwse-resize" }} onPointerDown={start("wh")} onClick={(e) => e.stopPropagation()}><title>Drag to change both</title></rect>
        </g>
      </svg>
    </div>
  );
}
