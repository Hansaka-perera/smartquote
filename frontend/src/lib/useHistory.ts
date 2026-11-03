import { useCallback, useRef, useState } from "react";

/** State with undo / redo. set() records history, replace() doesn't. */
export function useHistory<T>(initial: T) {
  const [state, setState] = useState<T>(initial);
  const past = useRef<T[]>([]);
  const future = useRef<T[]>([]);
  const [, bump] = useState(0);
  const set = useCallback((next: T | ((p: T) => T)) => {
    setState((cur) => {
      const n = typeof next === "function" ? (next as any)(cur) : next;
      if (JSON.stringify(n) === JSON.stringify(cur)) return cur;
      past.current.push(cur);
      if (past.current.length > 100) past.current.shift();
      future.current = [];
      return n;
    });
    bump((x) => x + 1);
  }, []);
  const undo = useCallback(() => {
    setState((cur) => {
      const p = past.current.pop();
      if (p === undefined) return cur;
      future.current.push(cur);
      return p;
    });
    bump((x) => x + 1);
  }, []);
  const redo = useCallback(() => {
    setState((cur) => {
      const f = future.current.pop();
      if (f === undefined) return cur;
      past.current.push(cur);
      return f;
    });
    bump((x) => x + 1);
  }, []);
  const reset = useCallback((v: T) => { past.current = []; future.current = []; setState(v); bump((x) => x + 1); }, []);
  return { state, set, undo, redo, reset, canUndo: past.current.length > 0, canRedo: future.current.length > 0 };
}
