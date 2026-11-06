import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { detectSource, type SourceKind } from './source';

const Ctx = createContext<SourceKind | null>(null);

export function DataSourceProvider({ children, initial }: { children: ReactNode; initial?: SourceKind }) {
  const [source, setSource] = useState<SourceKind | null>(initial ?? null);
  useEffect(() => {
    if (initial) return;
    let live = true;
    void detectSource().then((s) => live && setSource(s));
    return () => {
      live = false;
    };
  }, [initial]);
  return <Ctx.Provider value={source}>{children}</Ctx.Provider>;
}

/** null while the health check runs. */
export function useSource(): SourceKind | null {
  return useContext(Ctx);
}
