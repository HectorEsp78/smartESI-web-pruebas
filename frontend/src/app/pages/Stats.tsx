import { useCallback, useState } from 'react';
import { Header } from '../components/Header';
import { RangeProvider } from '../context/RangeContext';
import { SectionHeading } from '../components/ui/SectionHeading';
import { ElectricityDashboard } from '../components/stats/electricity/ElectricityDashboard';
import { LightingConsumptionChart } from '../components/stats/lighting/LightingConsumptionChart';
import { LightingBySpaceChart } from '../components/stats/lighting/LightingBySpaceChart';
import { LightingWasteChart } from '../components/stats/lighting/LightingWasteChart';
import { DEFAULT_TAB_ID } from '../lib/sections';
import type { DashboardTabId } from '../lib/sections';
import { parseDashboardUrlState, updateDashboardUrl } from '../lib/urlState';

const SECTION_CLASS = 'mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6 lg:px-8';

const TAB_HEADING: Record<DashboardTabId, { title: string; subtitle: string }> = {
  electricidad: {
    title: 'ELECTRICIDAD',
    subtitle:
      'Consumo o coste por edificio y por cuadros de planta, comparativa de periodos y base de centro cerrado.',
  },
  iluminacion: {
    title: 'ILUMINACIÓN',
    subtitle: 'Luminarias, su peso sobre el total y el despilfarro cuando no hay ocupación.',
  },
};

function TabContent({ tab }: { tab: DashboardTabId }) {
  if (tab === 'electricidad') {
    return <ElectricityDashboard />;
  }

  return (
    <div className="space-y-6">
      <LightingConsumptionChart />
      <LightingBySpaceChart />
      <LightingWasteChart />
    </div>
  );
}

function initialTab(): DashboardTabId {
  if (typeof window === 'undefined') return DEFAULT_TAB_ID;
  return parseDashboardUrlState(window.location.search).tab;
}

export function Stats() {
  const [activeTab, setActiveTab] = useState<DashboardTabId>(initialTab);
  const heading = TAB_HEADING[activeTab];

  const selectTab = useCallback((tab: DashboardTabId) => {
    setActiveTab(tab);
    updateDashboardUrl({ tab });
  }, []);

  return (
    <RangeProvider>
      <div className="app-shell min-h-screen">
        <Header activeTab={activeTab} onSelectTab={selectTab} />

        <main className="pb-16">
          <section className={SECTION_CLASS}>
            <SectionHeading title={heading.title} subtitle={heading.subtitle} />
            <TabContent tab={activeTab} />
          </section>
        </main>
      </div>
    </RangeProvider>
  );
}
