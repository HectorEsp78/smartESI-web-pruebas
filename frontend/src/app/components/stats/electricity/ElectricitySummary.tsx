import { StatCard } from '../../ui/StatCard';
import { formatElectricityValue } from '../../../lib/electricity';
import { formatPercent } from '../../../lib/format';
import { ELECTRICITY_GRANULARITY_NOUN } from '../../../types/electricity';
import type { ElectricityDto, ElectricityMetric } from '../../../types/electricity';

interface ElectricitySummaryProps {
  data: ElectricityDto | null;
  metric: ElectricityMetric;
}

export function ElectricitySummary({ data, metric }: ElectricitySummaryProps) {
  const unit = data?.unit ?? (metric === 'cost' ? '€' : 'kWh');
  const noun = data ? ELECTRICITY_GRANULARITY_NOUN[data.granularity] : 'intervalo';
  const total = data ? formatElectricityValue(data.stats.total, unit) : '—';
  const average = data ? formatElectricityValue(data.stats.average, unit) : '—';
  const minimum = data ? formatElectricityValue(data.stats.minimum, unit) : '—';
  const maximum = data ? formatElectricityValue(data.stats.maximum, unit) : '—';
  const baseline = data ? formatElectricityValue(data.stats.baseline_total, unit) : '—';
  const coverage = data ? formatPercent(data.sector_coverage * 100, 1) : '—';

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="Total"
          value={total}
          hint={data?.scope_label ?? 'Periodo seleccionado'}
          tone="primary"
        />
        <StatCard label={`Media por ${noun}`} value={average} hint="Media de los intervalos" />
        <StatCard label="Mínimo" value={minimum} hint={`Mínimo por ${noun}`} tone="success" />
        <StatCard label="Máximo" value={maximum} hint={`Máximo por ${noun}`} tone="accent" />
        <StatCard
          label="Base fuera de horario"
          value={baseline}
          hint={
            data
              ? `Proyección si el ámbito estuviera cerrado · ≈ ${formatElectricityValue(data.stats.baseline_hourly, unit)}/h`
              : 'Noches y fines de semana'
          }
          tone="warning"
        />
        <StatCard
          label="Cobertura de sectores"
          value={coverage}
          hint={
            data
              ? `Sectores: ${formatElectricityValue(data.sectors_total, unit)} de ${formatElectricityValue(data.fermin_total, unit)}`
              : 'Solo Fermín Caballero'
          }
        />
      </div>

      {data && data.sector_coverage < 0.999 && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900">
          Los cuadros de planta y el CPD son subcontadores parciales: cubren el{' '}
          {formatPercent(data.sector_coverage * 100, 1)} de Fermín Caballero. El resto se muestra
          como «No desglosado» y nunca se reparte como si fuera consumo medido.
        </p>
      )}
    </div>
  );
}
