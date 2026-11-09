import { WeatherMetric } from './WeatherMetric';
import {
  formatCorrelation,
  formatHumidity,
  formatPercent,
  formatPressure,
  formatSigned,
  formatTemperature,
  solarExposureHint,
} from '../../../lib/weather';
import type { MetricComparisonDto, WeatherComparisonDto } from '../../../types/weather';

interface WeatherComparisonProps {
  comparison: WeatherComparisonDto;
}

function ComparisonCard({
  title,
  unit,
  metric,
  format,
  hint,
  extra,
}: {
  title: string;
  unit: string;
  metric: MetricComparisonDto;
  format: (value: number | null) => string;
  hint?: string | null;
  extra: Array<{ label: string; value: string; hint?: string }>;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <h4 className="font-heading text-base font-semibold text-slate-900">{title}</h4>
      <p className="mb-3 text-xs text-muted-foreground">
        {metric.samples} horas comparadas · {format(metric.station_avg)} en la estación y{' '}
        {format(metric.aemet_avg)} en AEMET
      </p>
      <div className="grid grid-cols-2 gap-3">
        <WeatherMetric
          label="Diferencia media"
          value={formatSigned(metric.bias, unit)}
          hint="Estación − AEMET"
          tone="primary"
        />
        <WeatherMetric
          label="Error absoluto medio"
          value={format(metric.mean_absolute_error)}
          hint={`Correlación ${formatCorrelation(metric.correlation)}`}
        />
        {extra.map((item) => (
          <WeatherMetric key={item.label} label={item.label} value={item.value} hint={item.hint} />
        ))}
      </div>
      {hint && <p className="mt-3 text-xs text-slate-600">{hint}</p>}
    </div>
  );
}

export function WeatherComparison({ comparison }: WeatherComparisonProps) {
  const { temperature, humidity, pressure } = comparison;

  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <ComparisonCard
        title="Temperatura"
        unit="°C"
        metric={temperature}
        format={formatTemperature}
        hint={solarExposureHint(temperature.daytime_bias, temperature.nighttime_bias)}
        extra={[
          {
            label: 'De día (9–18 h)',
            value: formatSigned(temperature.daytime_bias, '°C'),
          },
          {
            label: 'De noche',
            value: formatSigned(temperature.nighttime_bias, '°C'),
          },
        ]}
      />
      <ComparisonCard
        title="Humedad relativa"
        unit="%"
        metric={humidity}
        format={formatHumidity}
        hint={
          humidity.saturated_pct !== null && humidity.saturated_pct >= 10
            ? 'Con el sensor saturado la estación marca 100 % aunque la humedad real sea menor: compara sobre todo la diferencia sin saturar.'
            : null
        }
        extra={[
          {
            label: 'Estación saturada',
            value: formatPercent(humidity.saturated_pct),
            hint: 'Horas al 99 % o más',
          },
          {
            label: 'Diferencia sin saturar',
            value: formatSigned(humidity.unsaturated_bias, '%'),
          },
        ]}
      />
      <ComparisonCard
        title="Presión"
        unit="hPa"
        metric={pressure}
        format={formatPressure}
        hint="La presión de la estación se reduce a la altitud del observatorio de AEMET (626 m)."
        extra={[]}
      />
    </div>
  );
}
