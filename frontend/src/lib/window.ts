export interface Panel { type: "sliding" | "fixed" | "casement"; direction: "left" | "right" }
export interface Cell { x: number; y: number; w: number; h: number; col: number; type: Panel["type"]; direction: Panel["direction"] }

/** Mirrors backend/app/services/drawing.py (y measured from the TOP here). */
export function geometry(width: number, height: number, panels: Panel[], transoms: number, frame: number, mullion: number): Cell[] {
  const rows = transoms + 1, n = panels.length;
  const pw = (width - 2 * frame - (n - 1) * mullion) / n;
  const ph = (height - 2 * frame - (rows - 1) * mullion) / rows;
  const cells: Cell[] = [];
  panels.forEach((p, i) => {
    for (let r = 0; r < rows; r++)
      cells.push({ x: frame + i * (pw + mullion), y: frame + r * (ph + mullion), w: pw, h: ph, col: i, type: p.type, direction: p.direction });
  });
  return cells;
}

export const toMm = (v: number, unit: string) => v * ({ mm: 1, cm: 10, m: 1000, in: 25.4, ft: 304.8 } as any)[unit];

