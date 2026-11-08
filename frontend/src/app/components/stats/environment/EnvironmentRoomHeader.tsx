import { Link } from 'react-router';
import type { DatePeriod } from '../../../lib/electricity';
import {
  QUALITY_BG_CLASS,
  QUALITY_TEXT_CLASS,
  formatCo2,
  formatHumidity,
  formatPresence,
  formatTemperature,
  formatUpdatedAt,
  isStaleTimestamp,
  roomColor,
} from '../../../lib/environment';
import { ENVIRONMENT_QUALITY_LABEL } from '../../../types/environment';
import type { EnvironmentQuality, EnvironmentRoomSummaryDto } from '../../../types/environment';

interface EnvironmentRoomHeaderProps {
  room: EnvironmentRoomSummaryDto;
  period: DatePeriod;
  dataSource: 'mock' | 'database';
}

interface CurrentMetric {
  label: string;
  value: string;
  quality?: EnvironmentQuality;
}

function indexHref(period: DatePeriod): string {
  const params = new URLSearchParams({ start: period.start, end: period.end });
  return `/infraestructura?${params.toString()}`;
}

function valueClass(quality: EnvironmentQuality | undefined): string {
  if (!quality || quality === 'unknown') return 'text-slate-900';
  return QUALITY_TEXT_CLASS[quality];
}

export function EnvironmentRoomHeader({ room, period, dataSource }: EnvironmentRoomHeaderProps) {
  const hasClimate = room.has_temperature || room.has_humidity || room.has_co2;
  const metrics: CurrentMetric[] = [];

  if (room.has_temperature) {
    metrics.push({
      label: 'Temperatura',
      value: formatTemperature(room.current_temperature_c),
      quality: room.temperature_status,
    });
  }
  if (room.has_humidity) {
    metrics.push({
      label: 'Humedad',
      value: formatHumidity(room.current_humidity_pct),
      quality: room.humidity_status,
    });
  }
  if (room.has_co2) {
    metrics.push({
      label: 'CO₂',
      value: formatCo2(room.current_co2_ppm),
      quality: room.co2_status,
    });
  }
  if (room.has_presence) {
    metrics.push({
      label: 'Presencia',
      value: formatPresence(room.current_presence),
      quality: room.current_presence ? 'good' : 'unknown',
    });
  }

  const hasEnvironmentalValues =
    room.current_temperature_c !== null ||
    room.current_humidity_pct !== null ||
    room.current_co2_ppm !== null;
  const stale = hasEnvironmentalValues && isStaleTimestamp(room.last_updated);
  const updatedText = hasEnvironmentalValues
    ? `Actualizado ${formatUpdatedAt(room.last_updated)}`
    : room.presence_updated_at
      ? `Presencia actualizada ${formatUpdatedAt(room.presence_updated_at)}`
      : 'Sin datos recientes';

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to={indexHref(period)}
            className="text-xs font-semibold text-primary hover:underline"
          >
            ← Volver a las estancias
          </Link>
          <div className="mt-1 flex items-center gap-2.5">
            <span
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: roomColor(room.room_id) }}
              aria-hidden="true"
            />
            <h3 className="font-heading text-2xl font-bold text-slate-900">{room.label}</h3>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {room.building_label} · {hasClimate ? 'Temperatura, humedad y CO₂' : 'Solo presencia'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {dataSource === 'mock' && (
            <span className="rounded-sm border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-600">
              Datos simulados
            </span>
          )}
          <span
            className={`rounded-sm border px-2.5 py-1 text-xs font-semibold ${QUALITY_BG_CLASS[room.comfort_status]}`}
          >
            {room.comfort_status === 'unknown'
              ? hasClimate
                ? 'Sin datos de confort'
                : 'Sin sensores ambientales'
              : `Confort ${ENVIRONMENT_QUALITY_LABEL[room.comfort_status].toLowerCase()}`}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-8 gap-y-3 rounded-md border border-slate-200 bg-white px-4 py-3">
        {metrics.length === 0 ? (
          <p className="text-sm text-slate-500">Sin datos de sensores.</p>
        ) : (
          metrics.map((metric) => (
            <div key={metric.label}>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                {metric.label}
              </span>
              <span className={`font-heading text-lg font-bold ${valueClass(metric.quality)}`}>
                {metric.value}
              </span>
            </div>
          ))
        )}
        <span
          className={`ml-auto text-xs ${stale ? 'font-semibold text-amber-700' : 'text-slate-500'}`}
        >
          {updatedText}
          {stale ? ' · sin actualizar' : ''}
        </span>
      </div>
    </div>
  );
}
