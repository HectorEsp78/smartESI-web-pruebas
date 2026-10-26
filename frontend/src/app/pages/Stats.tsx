import { useCallback, useState } from 'react';
import { Header } from '../components/Header';
import { RangeProvider } from '../context/RangeContext';
import { SectionHeading } from '../components/ui/SectionHeading';
import { OverviewSection } from '../components/stats/OverviewSection';
import { OccupancyAirQualityChart } from '../components/stats/OccupancyAirQualityChart';
import { ElectricityDashboard } from '../components/stats/electricity/ElectricityDashboard';
import { LightingConsumptionChart } from '../components/stats/lighting/LightingConsumptionChart';
import { LightingBySpaceChart } from '../components/stats/lighting/LightingBySpaceChart';
import { LightingWasteChart } from '../components/stats/lighting/LightingWasteChart';
import { GasConsumptionChart } from '../components/stats/climate/GasConsumptionChart';
import { ValvesTemperatureChart } from '../components/stats/climate/ValvesTemperatureChart';
import { EmptySpacesHeatingChart } from '../components/stats/climate/EmptySpacesHeatingChart';
import { DecisionsPanel } from '../components/stats/decisions/DecisionsPanel';
import { DEFAULT_TAB_ID } from '../lib/sections';
import type { DashboardTabId } from '../lib/sections';
import { parseDashboardUrlState, updateDashboardUrl } from '../lib/urlState';

const SECTION_CLASS = 'mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6 lg:px-8';

const TAB_HEADING: Record<DashboardTabId, { title: string; subtitle: string }> = {
  resumen: {
    title: 'RESUMEN',
    subtitle: 'Indicadores clave del centro en el periodo seleccionado.',
  },
  electricidad: {
    title: 'ELECTRICIDAD',
    subtitle: 'Consumo o coste por edificio y por cuadros de planta, comparativa de periodos y base de centro cerrado.',
  },
  iluminacion: {
    title: 'ILUMINACIÓN',
    subtitle: 'Luminarias, su peso sobre el total y el despilfarro cuando no hay ocupación.',
  },
  climatizacion: {
    title: 'CLIMATIZACIÓN Y GAS',
    subtitle: 'Gas frente al frío, respuesta de las electroválvulas y calefacción de aulas vacías.',
  },
  'ocupacion-aire': {
    title: 'OCUPACIÓN Y CALIDAD DEL AIRE',
    subtitle: 'Cruza la ocupación con el CO₂ para detectar patrones y ventilar a tiempo.',
  },
  decisiones: {
    title: 'DECISIONES',
    subtitle: 'Oportunidades de ahorro en luz y gas, con su impacto estimado en euros al año.',
  },
};

function TabContent({ tab }: { tab: DashboardTabId }) {
  switch (tab) {
    case 'electricidad':
      return <ElectricityDashboard />;
    case 'iluminacion':
      return (
        <div className="space-y-6">
          <LightingConsumptionChart />
          <LightingBySpaceChart />
          <LightingWasteChart />
        </div>
      );
    case 'climatizacion':
      return (
        <div className="space-y-6">
          <GasConsumptionChart />
          <ValvesTemperatureChart />
          <EmptySpacesHeatingChart />
        </div>
      );
    case 'ocupacion-aire':
      return <OccupancyAirQualityChart />;
    case 'decisiones':
      return <DecisionsPanel />;
    case 'resumen':
    default:
      return <OverviewSection />;
  }
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
