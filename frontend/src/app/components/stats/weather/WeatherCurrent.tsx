import type { ReactNode } from 'react';
import { formatTimestamp } from '../../../lib/format';
import {
  AEMET_COLOR,
  STATION_COLOR,
  currentStatusLabel,
  formatAge,
  formatHumidity,
  formatPercent,
  formatPmIndex,
  formatPressure,
  formatTemperature,
} from '../../../lib/weather';
import type { AemetLatestDto, WeatherCurrentDto } from '../../../types/weather';

interface WeatherCurrentProps {
  current: WeatherCurrentDto;
  aemet: AemetLatestDto;
}

function SourceCard({
  title,
  subtitle,
  color,
  badge,
  badgeWarning,
  temperature,
  humidity,
  pressure,
  footer,
  children,
}: {
  title: string;
  subtitle: string;
  color: string;
  badge: string;
  badgeWarning: boolean;
  temperature: number | null;
  humidity: number | null;
  pressure: string;
  footer: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-2 font-heading text-sm font-semibold text-slate-900">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: color }}
              aria-hidden="true"
            />
            {title}
          </p>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <span
          className={`rounded-sm border px-2 py-0.5 text-xs font-semibold ${
            badgeWarning
              ? 'border-amber-200 bg-amber-50 text-amber-800'
              : 'border-emerald-200 bg-emerald-50 text-emerald-700'
          }`}
        >
          {badge}
        </span>
      </div>
      <p className="mt-3 font-heading text-4xl font-bold text-slate-900">
        {formatTemperature(temperature)}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        {formatHumidity(humidity)} de humedad · {pressure}
      </p>
      {children}
      <p className="mt-2 text-xs text-slate-500">{footer}</p>
    </div>
  );
}

export function WeatherCurrent({ current, aemet }: WeatherCurrentProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <SourceCard
        title="Estación del centro"
        subtitle="Última lectura de weather.meteo"
        color={STATION_COLOR}
        badge={currentStatusLabel(current.status)}
        badgeWarning={current.status !== 'ok'}
        temperature={current.temperature_c}
        humidity={current.humidity_pct}
        pressure={`${formatPressure(current.pressure_hpa)} a nivel del mar`}
        footer={
          current.last_updated
            ? `${formatTimestamp(current.last_updated, 'd MMM yyyy, HH:mm')} (hace ${formatAge(current.age_hours)})`
            : 'Sin lectura'
        }
      >
        <p className="mt-1 text-xs text-slate-500">
          PM1 {formatPmIndex(current.pm1)} · PM2.5 {formatPmIndex(current.pm25)} · PM10{' '}
          {formatPmIndex(current.pm10)} (índice) · Batería {formatPercent(current.battery_pct)}
        </p>
      </SourceCard>

      <SourceCard
        title="AEMET · Ciudad Real"
        subtitle="Última observación guardada del observatorio"
        color={AEMET_COLOR}
        badge={aemet.stale ? 'Sin datos recientes' : 'Actualizada'}
        badgeWarning={aemet.stale}
        temperature={aemet.temperature_c}
        humidity={aemet.humidity_pct}
        pressure={`${formatPressure(aemet.pressure_hpa)} a 626 m`}
        footer={
          aemet.observed_at
            ? `${formatTimestamp(aemet.observed_at, 'd MMM yyyy, HH:mm')} (hace ${formatAge(aemet.age_hours)})`
            : 'Sin observaciones'
        }
      />
    </div>
  );
}
