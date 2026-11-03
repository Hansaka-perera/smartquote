export async function api<T = any>(path: string, opts: { method?: string; body?: any; form?: FormData } = {}): Promise<T> {
  const res = await fetch(path, {
    method: opts.method || (opts.body || opts.form ? "POST" : "GET"),
    headers: opts.body ? { "Content-Type": "application/json" } : undefined,
    body: opts.form ?? (opts.body ? JSON.stringify(opts.body) : undefined),
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      const d = j.detail;
      msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: any) => `${(x.loc || []).slice(1).join(".")}: ${x.msg}`).join("; ") : msg;
    } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

type Listener = (m: { text: string; kind: "ok" | "err" }) => void;
let toastL: Listener | null = null;
export const onToast = (l: Listener) => { toastL = l; };
export const toast = (text: string, kind: "ok" | "err" = "ok") => toastL?.({ text, kind });
