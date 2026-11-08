import { useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { Header } from '../components/Header';
import { RangeProvider } from '../context/RangeContext';
import { SectionHeading } from '../components/ui/SectionHeading';
import { ElectricityDashboard } from '../components/stats/electricity/ElectricityDashboard';
import { EnvironmentDashboard } from '../components/stats/environment/EnvironmentDashboard';
import { LightingConsumptionChart } from '../components/stats/lighting/LightingConsumptionChart';
import { LightingBySpaceChart } from '../components/stats/lighting/LightingBySpaceChart';
import { LightingWasteChart } from '../components/stats/lighting/LightingWasteChart';
import { MaintenanceDashboard } from '../components/stats/maintenance/MaintenanceDashboard';
import { WeatherDashboard } from '../components/stats/weather/WeatherDashboard';
import type { DashboardTabId } from '../lib/sections';
import { parseDashboardUrlState } from '../lib/urlState';

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
  infraestructura: {
    title: 'INFRAESTRUCTURA',
    subtitle:
      'Temperatura, humedad, CO₂ y presencia por estancia, con cruces para ahorro energético y decisiones.',
  },
  mantenimiento: {
    title: 'MANTENIMIENTO',
    subtitle:
      'Batería, transmisión y cortes por dispositivo para priorizar revisiones, cambios de batería y sustituciones.',
  },
  'medio-ambiente': {
    title: 'MEDIO AMBIENTE',
    subtitle:
      'Estación meteorológica del centro: temperatura, humedad, presión, partículas y cruces con el interior, AEMET y la energía.',
  },
};

function TabContent({ tab }: { tab: DashboardTabId }) {
  if (tab === 'electricidad') {
    return <ElectricityDashboard />;
  }

  if (tab === 'infraestructura') {
    return <EnvironmentDashboard />;
  }

  if (tab === 'mantenimiento') {
    return <MaintenanceDashboard />;
  }

  if (tab === 'medio-ambiente') {
    return <WeatherDashboard />;
  }

  return (
    <div className="space-y-6">
      <LightingConsumptionChart />
      <LightingBySpaceChart />
      <LightingWasteChart />
    </div>
  );
}

function tabFromLocation(pathname: string, search: string): DashboardTabId {
  if (pathname === '/infraestructura' || pathname.startsWith('/infraestructura/')) {
    return 'infraestructura';
  }
  return parseDashboardUrlState(search).tab;
}

export function Stats() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = tabFromLocation(location.pathname, location.search);
  const heading = TAB_HEADING[activeTab];

  const selectTab = useCallback(
    (tab: DashboardTabId) => {
      // Read the live search string: the range selector updates the URL with
      // ``history.replaceState``, which React Router's location may not have
      // observed yet.
      const currentSearch =
        typeof window === 'undefined' ? location.search : window.location.search;

      if (tab === 'infraestructura') {
        const params = new URLSearchParams(currentSearch);
        params.delete('tab');
        const search = params.toString();
        navigate(
          { pathname: '/infraestructura', search: search ? `?${search}` : '' },
          { replace: true },
        );
        return;
      }

      const params = new URLSearchParams(currentSearch);
      params.delete('start');
      params.delete('end');
      params.set('tab', tab);
      navigate({ pathname: '/', search: `?${params.toString()}` }, { replace: true });
    },
    [location.search, navigate],
  );

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
