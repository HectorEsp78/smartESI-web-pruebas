import { StatCard } from '../../ui/StatCard';
import { formatNumber, formatTimestamp } from '../../../lib/format';
import {
  currentStatusLabel,
  currentStatusTone,
  formatAgeHours,
  formatBattery,
  formatCorrelation,
  formatHumidity,
  formatPmIndex,
  formatPressure,
  formatSignedPressure,
  formatTemperature,
  pressureTrendLabel,
} from '../../../lib/weather';
import type { WeatherCurrentDto } from '../../../types/weather';

interface WeatherCurrentProps {
  current: WeatherCurrentDto;
}

const STATUS_CLASS: Record<'success' | 'warning' | 'neutral', string> = {
  success: 'border-success/30 bg-success/10 text-success',
  warning: 'border-warning/40 bg-warning/10 text-warning',
  neutral: 'border-slate-300 bg-slate-100 text-slate-600',
};

export function WeatherCurrent({ current }: WeatherCurrentProps) {
  const tone = currentStatusTone(current.status);

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
              Estación meteorológica · weather.meteo
            </p>
            <div className="mt-2 flex flex-wrap items-end gap-4">
              <p className="font-heading text-5xl font-bold text-slate-900">
                {formatTemperature(current.temperature_c)}
              </p>
              <div className="pb-1 text-sm text-slate-600">
                <p>{formatHumidity(current.humidity_pct)} de humedad</p>
                <p>{formatPressure(current.pressure_hpa)} a nivel del mar</p>
                <p className="text-xs text-slate-500">
                  {formatPressure(current.pressure_station_hpa)} a nivel de la estación
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 text-right">
            <span
              className={`rounded-sm border px-2 py-1 text-xs font-semibold ${STATUS_CLASS[tone]}`}
            >
              {currentStatusLabel(current.status)}
            </span>
            <p className="text-xs text-slate-500">
              {current.last_updated
                ? `Actualizado ${formatTimestamp(current.last_updated, 'd MMM HH:mm')}`
                : 'Sin lectura'}
            </p>
            {current.age_hours !== null && (
              <p className="text-xs text-slate-500">
                Hace {formatAgeHours(current.age_hours)}
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs text-slate-500">Punto de rocío</p>
            <p className="font-semibold text-slate-900">
              {formatTemperature(current.dew_point_c)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Humedad absoluta</p>
            <p className="font-semibold text-slate-900">
              {current.absolute_humidity_g_m3 === null
                ? '—'
                : `${formatNumber(current.absolute_humidity_g_m3, 1)} g/m³`}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Sensación térmica</p>
            <p className="font-semibold text-slate-900">
              {formatTemperature(current.heat_index_c)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Tendencia de presión (3 h)</p>
            <p className="font-semibold text-slate-900">
              {pressureTrendLabel(current.pressure_trend_3h_hpa)} ·{' '}
              {formatSignedPressure(current.pressure_trend_3h_hpa)}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="PM2.5 (índice)"
          value={formatPmIndex(current.pm25)}
          hint={`PM1 ${formatPmIndex(current.pm1)} · PM10 ${formatPmIndex(current.pm10)}`}
          tone="primary"
        />
        <StatCard
          label="Batería de la estación"
          value={formatBattery(current.battery_pct)}
          hint="Lectura del atributo Battery"
          tone={
            current.battery_pct === null
              ? 'neutral'
              : current.battery_pct <= 20
                ? 'warning'
                : 'success'
          }
        />
        <StatCard
          label="Tendencia 24 h"
          value={formatSignedPressure(current.pressure_trend_24h_hpa)}
          hint={pressureTrendLabel(current.pressure_trend_24h_hpa)}
          tone="neutral"
        />
        <StatCard
          label="Ratio PM2.5 / PM10"
          value={
            current.pm25_pm10_ratio === null
              ? '—'
              : formatCorrelation(current.pm25_pm10_ratio)
          }
          hint="Índice relativo, sin unidad publicada"
          tone="neutral"
        />
      </div>
    </div>
  );
}
