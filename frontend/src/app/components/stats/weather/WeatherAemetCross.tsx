import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { WeatherMetric } from './WeatherMetric';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { formatNumber, formatTimestamp } from '../../../lib/format';
import {
  aemetExposureLabel,
  formatCorrelation,
  formatKm,
  formatMm,
  formatSigned,
  formatSignedPressure,
  formatSignedTemperature,
  formatTemperature,
} from '../../../lib/weather';
import type { WeatherAemetCrossDto } from '../../../types/weather';

interface WeatherAemetCrossProps {
  cross: WeatherAemetCrossDto;
}

export function WeatherAemetCross({ cross }: WeatherAemetCrossProps) {
  const exposure = aemetExposureLabel(cross);
  const chartData = cross.hourly_bias.map((item) => ({
    hour: `${String(item.hour).padStart(2, '0')}:00`,
    bias: item.temperature_bias_c,
  }));

  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Estación vs. AEMET
          </h3>
          <p className="text-xs text-muted-foreground">
            Referencia externa de Ciudad Real, no la estación del centro.
          </p>
        </div>
        {cross.stale && (
          <span className="rounded-sm border border-warning/40 bg-warning/10 px-2 py-1 text-xs font-semibold text-warning">
            AEMET desactualizada
          </span>
        )}
      </div>

      {!cross.available ? (
        <p className="py-6 text-sm text-slate-500">
          No hay lecturas solapadas de AEMET para el periodo seleccionado.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <WeatherMetric
              label="Sesgo de temperatura"
              value={formatSignedTemperature(cross.temperature_bias_c)}
              hint="Estación − AEMET"
              tone="primary"
            />
            <WeatherMetric
              label="Error absoluto medio"
              value={formatTemperature(cross.temperature_mae_c)}
              hint={`Correlación ${formatCorrelation(cross.temperature_correlation)}`}
              tone="neutral"
            />
            <WeatherMetric
              label="Sesgo de humedad"
              value={
                cross.humidity_bias_pct === null
                  ? '—'
                  : `${formatSigned(cross.humidity_bias_pct, 1)} %`
              }
              hint={`MAE ${cross.humidity_mae_pct === null ? '—' : `${formatNumber(cross.humidity_mae_pct, 1)} %`}`}
              tone="neutral"
            />
            <WeatherMetric
              label="Sesgo de presión"
              value={formatSignedPressure(cross.pressure_bias_hpa)}
              hint={`Correlación ${formatCorrelation(cross.pressure_correlation)}`}
              tone="neutral"
            />
            <WeatherMetric
              label="Sesgo diurno (9–18 h)"
              value={formatSignedTemperature(cross.daytime_temperature_bias_c)}
              hint="Si es mucho mayor que el nocturno, puede haber sol directo"
              tone="warning"
            />
            <WeatherMetric
              label="Sesgo nocturno"
              value={formatSignedTemperature(cross.nighttime_temperature_bias_c)}
              hint="Referencia sin radiación solar"
              tone="neutral"
            />
            <WeatherMetric
              label="Precipitación AEMET"
              value={formatMm(cross.precipitation_mm)}
              hint="Acumulada en el periodo"
              tone="neutral"
            />
            <WeatherMetric
              label="Visibilidad mínima"
              value={formatKm(cross.visibility_min_km)}
              hint={`Última lectura: ${cross.last_updated ? formatTimestamp(cross.last_updated, 'd MMM HH:mm') : '—'}`}
              tone="neutral"
            />
          </div>

          <div className="mt-4 border-t border-slate-100 pt-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.06em] text-slate-500">
              Sesgo térmico por hora del día
            </p>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="hour"
                    tick={AXIS_TICK}
                    tickLine={AXIS_LINE}
                    axisLine={AXIS_LINE}
                    interval={3}
                  />
                  <YAxis
                    tickFormatter={(value) => formatNumber(Number(value), 0)}
                    tick={AXIS_TICK}
                    tickLine={AXIS_LINE}
                    axisLine={AXIS_LINE}
                    width={36}
                  />
                  <ReferenceLine y={0} stroke="#64748b" />
                  <Tooltip
                    contentStyle={TOOLTIP_STYLE}
                    formatter={(value) => [
                      `${formatNumber(Number(value), 1)} °C`,
                      'Sesgo',
                    ]}
                    labelFormatter={(value) => `Hora ${value}`}
                  />
                  <Bar
                    dataKey="bias"
                    name="Sesgo"
                    fill="#cf6c2e"
                    isAnimationActive={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {exposure && (
            <p className="mt-3 text-xs text-slate-600">{exposure}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">
            {cross.samples} horas comparadas.
          </p>
        </>
      )}
    </div>
  );
}
