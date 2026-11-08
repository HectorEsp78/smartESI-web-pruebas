import { WeatherMetric } from './WeatherMetric';
import { formatNumber } from '../../../lib/format';
import { formatCorrelation } from '../../../lib/weather';
import type { WeatherPmCrossDto } from '../../../types/weather';

interface WeatherPmCrossProps {
  cross: WeatherPmCrossDto;
}

export function WeatherPmCross({ cross }: WeatherPmCrossProps) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-4">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Partículas y ambiente
        </h3>
        <p className="text-xs text-muted-foreground">
          Relaciones del índice de partículas con humedad, temperatura y aire interior.
        </p>
      </div>

      {!cross.available ? (
        <p className="py-6 text-sm text-slate-500">
          No hay datos de partículas suficientes para el periodo seleccionado.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <WeatherMetric
              label="PM2.5 medio"
              value={cross.pm25_avg === null ? '—' : formatNumber(cross.pm25_avg, 0)}
              hint="Índice relativo, sin unidad publicada"
              tone="accent"
            />
            <WeatherMetric
              label="PM10 medio"
              value={cross.pm10_avg === null ? '—' : formatNumber(cross.pm10_avg, 0)}
              hint="Índice relativo"
              tone="neutral"
            />
            <WeatherMetric
              label="Ratio PM2.5 / PM10"
              value={
                cross.pm25_pm10_ratio === null
                  ? '—'
                  : formatNumber(cross.pm25_pm10_ratio, 2)
              }
              hint="Cercano a 1 en esta estación"
              tone="neutral"
            />
            <WeatherMetric
              label="Ratio PM1 / PM2.5"
              value={
                cross.pm1_pm25_ratio === null
                  ? '—'
                  : formatNumber(cross.pm1_pm25_ratio, 2)
              }
              hint="Cercano a 1 en esta estación"
              tone="neutral"
            />
            <WeatherMetric
              label="Correlación con humedad"
              value={formatCorrelation(cross.humidity_correlation)}
              hint="Positiva: humedad y partículas suben juntas"
              tone="primary"
            />
            <WeatherMetric
              label="Correlación con temperatura"
              value={formatCorrelation(cross.temperature_correlation)}
              hint="Negativa: más calor, menos índice"
              tone="primary"
            />
            <WeatherMetric
              label="Correlación con CO₂ interior"
              value={formatCorrelation(cross.co2_correlation)}
              hint="Ventilación y ocupación"
              tone="neutral"
            />
            <WeatherMetric
              label="Correlación con TVOC interior"
              value={formatCorrelation(cross.tvoc_correlation)}
              hint="Compuestos orgánicos volátiles"
              tone="neutral"
            />
          </div>
          <p className="mt-3 text-xs text-slate-500">{cross.caveat}</p>
        </>
      )}
    </div>
  );
}
