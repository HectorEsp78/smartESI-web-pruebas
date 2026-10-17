import { useState } from 'react';
import { Header } from '../components/Header';
import { RangeProvider } from '../context/RangeContext';
import { SectionHeading } from '../components/ui/SectionHeading';
import { OverviewSection } from '../components/stats/OverviewSection';
import { EnergyConsumptionChart } from '../components/stats/EnergyConsumptionChart';
import { EnergyByBuildingChart } from '../components/stats/EnergyByBuildingChart';
import { OccupancyAirQualityChart } from '../components/stats/OccupancyAirQualityChart';
import { EnergyBreakdownChart } from '../components/stats/electricity/EnergyBreakdownChart';
import { EnergyCompareChart } from '../components/stats/electricity/EnergyCompareChart';
import { EnergyEfficiencyChart } from '../components/stats/electricity/EnergyEfficiencyChart';
import { LightingConsumptionChart } from '../components/stats/lighting/LightingConsumptionChart';
import { LightingBySpaceChart } from '../components/stats/lighting/LightingBySpaceChart';
import { LightingWasteChart } from '../components/stats/lighting/LightingWasteChart';
import { GasConsumptionChart } from '../components/stats/climate/GasConsumptionChart';
import { ValvesTemperatureChart } from '../components/stats/climate/ValvesTemperatureChart';
import { EmptySpacesHeatingChart } from '../components/stats/climate/EmptySpacesHeatingChart';
import { DecisionsPanel } from '../components/stats/decisions/DecisionsPanel';
import { DEFAULT_TAB_ID } from '../lib/sections';
import type { DashboardTabId } from '../lib/sections';

const SECTION_CLASS = 'mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6 lg:px-8';

const TAB_HEADING: Record<DashboardTabId, { title: string; subtitle: string }> = {
  resumen: {
    title: 'RESUMEN',
    subtitle: 'Indicadores clave del centro en el periodo seleccionado.',
  },
  electricidad: {
    title: 'ELECTRICIDAD',
    subtitle: 'Consumo, carga base, comparativa con el periodo anterior y eficiencia por superficie.',
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
      return (
        <div className="space-y-6">
          <EnergyConsumptionChart />
          <EnergyBreakdownChart />
          <EnergyCompareChart />
          <EnergyEfficiencyChart />
          <EnergyByBuildingChart />
        </div>
      );
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

export function Stats() {
  const [activeTab, setActiveTab] = useState<DashboardTabId>(DEFAULT_TAB_ID);
  const heading = TAB_HEADING[activeTab];

  return (
    <RangeProvider>
      <div className="app-shell min-h-screen">
        <Header activeTab={activeTab} onSelectTab={setActiveTab} />

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
