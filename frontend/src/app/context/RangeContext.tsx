import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { updateDashboardUrl, parseDashboardUrlState } from '../lib/urlState';
import { DEFAULT_DASHBOARD_RANGE } from '../types/range';
import type { DashboardRange } from '../types/range';

interface RangeContextValue {
  range: DashboardRange;
  setRange: (range: DashboardRange) => void;
}

const RangeContext = createContext<RangeContextValue | null>(null);

function initialRange(): DashboardRange {
  if (typeof window === 'undefined') return DEFAULT_DASHBOARD_RANGE;
  return parseDashboardUrlState(window.location.search).range;
}

export function RangeProvider({ children }: { children: ReactNode }) {
  const [range, setRangeState] = useState<DashboardRange>(initialRange);

  const setRange = useCallback((nextRange: DashboardRange) => {
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
