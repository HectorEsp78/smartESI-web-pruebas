import { StatCard } from '../../ui/StatCard';
import { formatNumber } from '../../../lib/format';
import {
  formatHours,
  formatHumidity,
  formatPmIndex,
  formatPressure,
  formatTemperature,
} from '../../../lib/weather';
import type { WeatherSummaryDto } from '../../../types/weather';

interface WeatherSummaryProps {
  summary: WeatherSummaryDto;
}

export function WeatherSummary({ summary }: WeatherSummaryProps) {
  const coverageTone =
    summary.coverage_pct === null
      ? 'neutral'
      : summary.coverage_pct < 80
        ? 'warning'
        : 'success';

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Cobertura de la estación"
        value={
          summary.coverage_pct === null
            ? '—'
            : `${formatNumber(summary.coverage_pct, 1)} %`
        }
        hint={`${summary.samples} muestras · ${formatHours(summary.outage_hours)} sin datos`}
        tone={coverageTone}
      />
      <StatCard
        label="Temperatura media"
        value={formatTemperature(summary.temperature_avg_c)}
        hint={`Mín. ${formatTemperature(summary.temperature_min_c)} · Máx. ${formatTemperature(summary.temperature_max_c)}`}
        tone="primary"
      />
      <StatCard
        label="Amplitud diaria media"
        value={formatTemperature(summary.temperature_amplitude_avg_c)}
        hint={`${summary.tropical_nights} noches tropicales (≥ 20 °C)`}
        tone="neutral"
      />
      <StatCard
        label="Humedad media"
        value={formatHumidity(summary.humidity_avg_pct)}
        hint={`Mín. ${formatHumidity(summary.humidity_min_pct)} · Máx. ${formatHumidity(summary.humidity_max_pct)}`}
        tone="primary"
      />
      <StatCard
        label="Presión media"
        value={formatPressure(summary.pressure_avg_hpa)}
        hint={`Rango ${formatPressure(summary.pressure_range_hpa)}`}
        tone="neutral"
      />
      <StatCard
        label="Horas de calor / frío"
        value={`${formatHours(summary.hot_hours)} / ${formatHours(summary.cold_hours)}`}
        hint="≥ 30 °C / ≤ 10 °C"
        tone={summary.hot_hours !== null && summary.hot_hours > 0 ? 'warning' : 'neutral'}
      />
      <StatCard
        label="Grados-día"
        value={`${summary.heating_degree_days === null ? '—' : formatNumber(summary.heating_degree_days, 1)} HDD`}
        hint={`${summary.cooling_degree_days === null ? '—' : formatNumber(summary.cooling_degree_days, 1)} CDD · bases 18 / 22 °C`}
        tone="neutral"
      />
      <StatCard
        label="PM2.5 (índice)"
        value={formatPmIndex(summary.pm25_avg)}
        hint={`Máx. ${formatPmIndex(summary.pm25_max)} · índice relativo`}
        tone="accent"
      />
    </div>
  );
}
