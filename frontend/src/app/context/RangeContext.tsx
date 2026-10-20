import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { updateDashboardUrl, parseDashboardUrlState } from '../lib/urlState';
import { DEFAULT_ENERGY_RANGE } from '../types/energy';
import type { EnergyRange } from '../types/energy';

interface RangeContextValue {
  range: EnergyRange;
  setRange: (range: EnergyRange) => void;
}

const RangeContext = createContext<RangeContextValue | null>(null);

function initialRange(): EnergyRange {
  if (typeof window === 'undefined') return DEFAULT_ENERGY_RANGE;
  return parseDashboardUrlState(window.location.search).range;
}

export function RangeProvider({ children }: { children: ReactNode }) {
  const [range, setRangeState] = useState<EnergyRange>(initialRange);

  const setRange = useCallback((nextRange: EnergyRange) => {
    setRangeState(nextRange);
    updateDashboardUrl({ range: nextRange });
  }, []);

  const value = useMemo(() => ({ range, setRange }), [range, setRange]);
  return <RangeContext.Provider value={value}>{children}</RangeContext.Provider>;
}

export function useGlobalRange(): RangeContextValue {
  const context = useContext(RangeContext);
  if (!context) {
    throw new Error('useGlobalRange debe usarse dentro de <RangeProvider>.');
  }
  return context;
}
