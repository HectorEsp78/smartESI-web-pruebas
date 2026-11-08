import { Link } from 'react-router';
import type { DatePeriod } from '../../../lib/electricity';
import {
  QUALITY_BG_CLASS,
  QUALITY_DOT_CLASS,
  formatCo2,
  formatHumidity,
  formatOccupancy,
  formatTemperature,
  formatUpdatedAt,
  isStaleTimestamp,
  roomColor,
} from '../../../lib/environment';
import { ENVIRONMENT_QUALITY_LABEL } from '../../../types/environment';
import type { EnvironmentRoomSummaryDto } from '../../../types/environment';

interface EnvironmentRoomListProps {
  rooms: EnvironmentRoomSummaryDto[];
  period: DatePeriod;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
}

function roomHref(roomId: string, period: DatePeriod): string {
  const params = new URLSearchParams({ start: period.start, end: period.end });
  return `/infraestructura/${encodeURIComponent(roomId)}?${params.toString()}`;
}

function presenceLabel(value: boolean | null): string {
  if (value === null) return '—';
  return value ? 'Ocupada' : 'Libre';
}

export function EnvironmentRoomList({
  rooms,
  period,
  isLoading,
  error,
  onRetry,
}: EnvironmentRoomListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white py-16">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/35 bg-white p-5">
        <p className="font-semibold text-destructive">No se pudieron cargar las estancias.</p>
        <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (rooms.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        No hay estancias confirmadas para mostrar.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
      <table className="w-full min-w-[680px] border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
            <th className="px-4 py-2">Espacio</th>
            <th className="px-4 py-2">Ambiente actual</th>
            <th className="px-4 py-2">Uso</th>
            <th className="px-4 py-2">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rooms.map((room) => {
            const hasClimate = room.has_temperature || room.has_humidity || room.has_co2;
            const environment = [
              room.has_temperature ? formatTemperature(room.current_temperature_c) : null,
              room.has_humidity ? formatHumidity(room.current_humidity_pct) : null,
              room.has_co2 ? formatCo2(room.current_co2_ppm) : null,
            ]
              .filter((value): value is string => value !== null)
              .join(' · ');
            const hasEnvironmentalValue =
              room.current_temperature_c !== null ||
              room.current_humidity_pct !== null ||
              room.current_co2_ppm !== null;
            const stale = hasEnvironmentalValue && isStaleTimestamp(room.last_updated);

            return (
              <tr key={room.room_id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/70">
                <td className="px-4 py-3">
                  <Link
                    to={roomHref(room.room_id, period)}
                    className="group flex items-start gap-2.5"
                  >
                    <span
                      className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: roomColor(room.room_id) }}
                      aria-hidden="true"
                    />
                    <span>
                      <span className="block font-heading text-sm font-semibold text-slate-900 group-hover:text-primary">
                        {room.label}
                      </span>
                      <span className="block text-[11px] text-slate-500">
                        {room.building_label}
                        {!hasClimate ? ' · solo presencia' : ''}
                      </span>
                      {stale && (
                        <span className="mt-0.5 block text-[11px] font-semibold text-amber-700">
                          Sin actualizar · {formatUpdatedAt(room.last_updated)}
                        </span>
                      )}
                    </span>
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <p className={`text-sm ${hasClimate ? 'text-slate-800' : 'text-slate-400'}`}>
                    {hasClimate ? environment || 'Sin dato' : 'Solo presencia'}
                  </p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-slate-800">{presenceLabel(room.current_presence)}</p>
                  <p className="text-[11px] text-slate-500">
                    {room.occupancy_pct === null
                      ? 'Sin ocupación'
                      : `${formatOccupancy(room.occupancy_pct)} del periodo`}
                  </p>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-[11px] font-semibold ${QUALITY_BG_CLASS[room.comfort_status]}`}
                  >
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${QUALITY_DOT_CLASS[room.comfort_status]}`}
                      aria-hidden="true"
                    />
                    {room.comfort_status === 'unknown' && !hasClimate
                      ? 'Solo presencia'
                      : ENVIRONMENT_QUALITY_LABEL[room.comfort_status]}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
