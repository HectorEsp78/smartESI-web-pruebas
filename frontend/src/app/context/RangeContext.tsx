import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { DEFAULT_ENERGY_RANGE } from '../types/energy';
import type { EnergyRange } from '../types/energy';

interface RangeContextValue {
  range: EnergyRange;
  setRange: (range: EnergyRange) => void;
}

const RangeContext = createContext<RangeContextValue | null>(null);

export function RangeProvider({ children }: { children: ReactNode }) {
  const [range, setRange] = useState<EnergyRange>(DEFAULT_ENERGY_RANGE);
  const value = useMemo(() => ({ range, setRange }), [range]);
  return <RangeContext.Provider value={value}>{children}</RangeContext.Provider>;
}

export function useGlobalRange(): RangeContextValue {
  const context = useContext(RangeContext);
  if (!context) {
    throw new Error('useGlobalRange debe usarse dentro de <RangeProvider>.');
  }
  return context;
}
