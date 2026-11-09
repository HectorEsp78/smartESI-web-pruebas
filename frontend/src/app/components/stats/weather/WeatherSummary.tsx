import { StatCard } from '../../ui/StatCard';
import { formatNumber } from '../../../lib/format';
import {
  formatHumidity,
  formatMm,
  formatPercent,
  formatPmIndex,
  formatPressure,
  formatTemperature,
} from '../../../lib/weather';
import type { WeatherSummaryDto } from '../../../types/weather';

interface WeatherSummaryProps {
  summary: WeatherSummaryDto;
}

export function WeatherSummary({ summary }: WeatherSummaryProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Temperatura media"
        value={formatTemperature(summary.temperature_avg_c)}
        hint={`Mín. ${formatTemperature(summary.temperature_min_c)} · Máx. ${formatTemperature(summary.temperature_max_c)}`}
        tone="primary"
      />
      <StatCard
        label="Humedad media"
        value={formatHumidity(summary.humidity_avg_pct)}
        hint={`Mín. ${formatHumidity(summary.humidity_min_pct)} · Máx. ${formatHumidity(summary.humidity_max_pct)}`}
      />
      <StatCard
        label="Presión media"
        value={formatPressure(summary.pressure_avg_hpa)}
        hint="A nivel del mar"
      />
      <StatCard
        label="Lecturas de la estación"
        value={formatNumber(summary.samples, 0)}
        hint={`Cobertura ${formatPercent(summary.coverage_pct)} del periodo`}
      />
      <StatCard
        label="PM2.5 medio (índice)"
        value={formatPmIndex(summary.pm25_avg)}
        hint={`PM10 ${formatPmIndex(summary.pm10_avg)} · Sin unidad publicada`}
      />
      <StatCard
        label="Batería mínima"
        value={formatPercent(summary.battery_min_pct)}
        hint="De la estación en el periodo"
      />
      <StatCard
        label="Lluvia en Ciudad Real"
        value={formatMm(summary.aemet_precipitation_mm)}
        hint={`${summary.aemet_rainy_hours} horas con lluvia, según AEMET`}
      />
    </div>
  );
}
