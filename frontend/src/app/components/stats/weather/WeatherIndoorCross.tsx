import { WeatherMetric } from './WeatherMetric';
import {
  formatCorrelation,
  formatHumidity,
  formatPmIndex,
  formatPressure,
  formatSigned,
  formatSignedPressure,
  formatSignedTemperature,
  formatTemperature,
} from '../../../lib/weather';
import type { WeatherIndoorCrossDto } from '../../../types/weather';

interface WeatherIndoorCrossProps {
  cross: WeatherIndoorCrossDto;
}

export function WeatherIndoorCross({ cross }: WeatherIndoorCrossProps) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-4">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Exterior vs. interior
        </h3>
        <p className="text-xs text-muted-foreground">
          Cruce con sensor.ambiente, el sensor interior de referencia.
        </p>
      </div>

      {!cross.available ? (
        <p className="py-6 text-sm text-slate-500">
          No hay suficientes lecturas interiores para cruzar con la estación.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <WeatherMetric
              label="Temperatura interior"
              value={formatTemperature(cross.current_temperature_c)}
              hint={`Media del periodo: ${formatTemperature(cross.avg_temperature_c)}`}
              tone="primary"
            />
            <WeatherMetric
              label="Humedad interior"
              value={formatHumidity(cross.current_humidity_pct)}
              hint={`Media del periodo: ${formatHumidity(cross.avg_humidity_pct)}`}
              tone="primary"
            />
            <WeatherMetric
              label="CO₂ interior"
              value={formatPmIndex(cross.current_co2_ppm)}
              hint={`Media: ${formatPmIndex(cross.avg_co2_ppm)} ppm`}
              tone="neutral"
            />
            <WeatherMetric
              label="TVOC interior"
              value={formatPmIndex(cross.current_tvoc)}
              hint={`Media: ${formatPmIndex(cross.avg_tvoc)}`}
              tone="neutral"
            />
            <WeatherMetric
              label="Salto térmico exterior − interior"
              value={formatSignedTemperature(cross.outdoor_minus_indoor_c)}
              hint="Negativo: el exterior está más frío"
              tone={
                cross.outdoor_minus_indoor_c !== null &&
                cross.outdoor_minus_indoor_c < 0
                  ? 'warning'
                  : 'neutral'
              }
            />
            <WeatherMetric
              label="Salto de humedad exterior − interior"
              value={
                cross.outdoor_minus_indoor_humidity_pct === null
                  ? '—'
                  : `${formatSigned(cross.outdoor_minus_indoor_humidity_pct, 1)} %`
              }
              hint="Positivo: el exterior está más húmedo"
              tone="neutral"
            />
            <WeatherMetric
              label="Correlación de temperatura"
              value={formatCorrelation(cross.temperature_correlation)}
              hint="0 = sin relación; 1 = relación perfecta"
              tone="accent"
            />
            <WeatherMetric
              label="Presión interior − estación"
              value={formatSignedPressure(cross.pressure_bias_hpa)}
              hint={`Interior medio: ${formatPressure(cross.avg_pressure_hpa)}`}
              tone="neutral"
            />
          </div>
          <p className="mt-3 text-xs text-slate-500">
            {cross.samples} horas comparadas. La correlación de humedad es{' '}
            {formatCorrelation(cross.humidity_correlation)}.
          </p>
        </>
      )}
    </div>
  );
}
