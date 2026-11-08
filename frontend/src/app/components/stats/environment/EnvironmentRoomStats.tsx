import { StatCard } from '../../ui/StatCard';
import {
  formatCo2,
  formatHours,
  formatHumidity,
  formatOccupancy,
  formatTemperature,
} from '../../../lib/environment';
import { formatNumber } from '../../../lib/format';
import type { EnvironmentRoomSummaryDto } from '../../../types/environment';

interface EnvironmentRoomStatsProps {
  room: EnvironmentRoomSummaryDto;
}

function rangeText(
  minimum: number | null,
  maximum: number | null,
  unit: string,
  digits: number,
): string {
  if (minimum === null || maximum === null) return 'Sin rango';
  return `Rango ${formatNumber(minimum, digits)} – ${formatNumber(maximum, digits)} ${unit}`;
}

export function EnvironmentRoomStats({ room }: EnvironmentRoomStatsProps) {
  const hasTemperature = room.avg_temperature_c !== null;
  const hasHumidity = room.avg_humidity_pct !== null;
  const hasCo2 = room.avg_co2_ppm !== null;
  const hasPresence = room.occupancy_pct !== null;

  if (!hasTemperature && !hasHumidity && !hasCo2 && !hasPresence) {
    return (
      <p className="rounded-md border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-500">
        No hay datos suficientes para resumir el periodo.
      </p>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {hasTemperature && (
        <StatCard
          label="Temperatura media"
          value={formatTemperature(room.avg_temperature_c)}
          hint={rangeText(room.min_temperature_c, room.max_temperature_c, '°C', 1)}
        />
      )}
      {hasHumidity && (
        <StatCard
          label="Humedad media"
          value={formatHumidity(room.avg_humidity_pct)}
          hint={rangeText(room.min_humidity_pct, room.max_humidity_pct, '%', 0)}
        />
      )}
      {hasCo2 && (
        <StatCard
          label="CO₂ medio"
          value={formatCo2(room.avg_co2_ppm)}
          hint={
            room.peak_co2_ppm === null
              ? 'Sin pico registrado'
              : `Pico ${formatCo2(room.peak_co2_ppm)}`
          }
          tone={
            room.avg_co2_ppm === null
              ? 'neutral'
              : room.avg_co2_ppm > 800
                ? 'warning'
                : 'success'
          }
        />
      )}
      {hasPresence && (
        <StatCard
          label="Ocupación media"
          value={formatOccupancy(room.occupancy_pct)}
          hint={`${formatHours(room.occupied_hours)} ocupadas`}
          tone="primary"
        />
      )}
    </div>
  );
}
