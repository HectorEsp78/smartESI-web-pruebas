import { useState } from 'react';
import { ElectricityBuildingsChart } from './ElectricityBuildingsChart';
import { ElectricityComparisonChart } from './ElectricityComparisonChart';
import { ElectricityFilters } from './ElectricityFilters';
import { ElectricitySectorsChart } from './ElectricitySectorsChart';
import { ElectricitySummary } from './ElectricitySummary';
import { useElectricityMeta, useElectricityStats } from '../../../hooks/useElectricity';
import {
  defaultElectricityPeriod,
  granularityForPeriod,
  isValidPeriod,
} from '../../../lib/electricity';
import { formatNumber } from '../../../lib/format';
import {
  DEFAULT_ELECTRICITY_METRIC,
  ELECTRICITY_ALL,
  FERMIN_BUILDING_ID,
} from '../../../types/electricity';
import type { ElectricityMetric } from '../../../types/electricity';

export function ElectricityDashboard() {
  const [period, setPeriod] = useState(() => defaultElectricityPeriod(30));
  const [metric, setMetric] = useState<ElectricityMetric>(DEFAULT_ELECTRICITY_METRIC);
  const [building, setBuilding] = useState<string>(ELECTRICITY_ALL);
  const [sector, setSector] = useState('');

  const metaResult = useElectricityMeta();
  const validPeriod = isValidPeriod(period);
  const granularity = granularityForPeriod(period);
  const query = validPeriod
    ? {
        start: period.start,
        end: period.end,
        granularity,
        metric,
        building,
        sector: building === FERMIN_BUILDING_ID && sector ? sector : undefined,
      }
    : null;
  const statsResult = useElectricityStats(query);
  // Never keep showing the previous range while the user is editing an
  // invalid period (for example, after clearing one of the date inputs).
  const statsData = validPeriod ? statsResult.data : null;

  const changeBuilding = (value: string) => {
    setBuilding(value);
    if (value !== FERMIN_BUILDING_ID) setSector('');
  };

  const dataSource = metaResult.data?.data_source;
  const sourceLabel =
    dataSource === 'database'
      ? 'Datos reales del recorder de Home Assistant (solo lectura).'
      : dataSource === 'mock'
        ? 'Datos simulados: el backend está en modo mock.'
        : 'Datos servidos por el backend configurado.';
  const appliedPrice =
    statsData?.price_eur_per_kwh ?? metaResult.data?.price_eur_per_kwh ?? null;
  const priceLabel = appliedPrice !== null ? `${formatNumber(appliedPrice, 3)} €/kWh` : '—';

  return (
    <div className="space-y-6">
      <p className="max-w-4xl text-sm text-slate-600">
        <strong>{sourceLabel}</strong>{' '}
        {metric === 'cost' ? (
          <>
            El coste se calcula con la tarifa real del cuadro general (
            <strong>{priceLabel}</strong>).
          </>
        ) : (
          <>Cambia a «Coste» para ver el importe con la tarifa real del cuadro general.</>
        )}{' '}
        Fermín Caballero se obtiene como Cuadro General − Módulo A − Módulo B; los cuadros de
        planta y el CPD son subcontadores parciales de ese edificio.
      </p>

      <ElectricityFilters
        meta={metaResult.data}
        start={period.start}
        end={period.end}
        metric={metric}
        building={building}
        sector={sector}
        priceEurPerKwh={appliedPrice}
        onStartChange={(start) => setPeriod((current) => ({ ...current, start }))}
        onEndChange={(end) => setPeriod((current) => ({ ...current, end }))}
        onMetricChange={setMetric}
        onBuildingChange={changeBuilding}
        onSectorChange={setSector}
      />

      {metaResult.error && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900">
          No se pudieron cargar los edificios y sectores: {metaResult.error.message}. Se muestra el
          ámbito «Todos los edificios».
        </p>
      )}

      <ElectricitySummary data={statsData} metric={metric} />

      <ElectricityBuildingsChart
        data={statsData}
        isLoading={statsResult.isLoading}
        isFetching={statsResult.isFetching}
        error={statsResult.error}
        retry={statsResult.retry}
      />

      <ElectricitySectorsChart
        data={statsData}
        isLoading={statsResult.isLoading}
        isFetching={statsResult.isFetching}
        error={statsResult.error}
        retry={statsResult.retry}
      />

      <ElectricityComparisonChart
        mainPeriod={period}
        granularity={granularity}
        metric={metric}
        building={building}
        sector={building === FERMIN_BUILDING_ID ? sector : ''}
        stats={statsData}
        meta={metaResult.data}
      />
    </div>
  );
}
