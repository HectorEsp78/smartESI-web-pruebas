import { formatNumber } from '../../../lib/format';
import {
  formatCo2,
  formatHumidity,
  formatOccupancy,
  formatTemperature,
} from '../../../lib/environment';
import type {
  EnvironmentBenchmarkDto,
  EnvironmentRoomSummaryDto,
} from '../../../types/environment';

interface Props {
  room: EnvironmentRoomSummaryDto;
  benchmark: EnvironmentBenchmarkDto;
}

interface Row {
  label: string;
  roomValue: number | null;
  average: number | null;
  format: (value: number | null) => string;
  rooms: number;
  lowerIsBetter?: boolean;
}

function deltaText(value: number, unit: string, digits = 1): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, digits)} ${unit}`;
}

export function EnvironmentBenchmarkCard({ room, benchmark }: Props) {
  const rows: Row[] = [
    {
      label: 'Temperatura',
      roomValue: room.avg_temperature_c,
      average: benchmark.avg_temperature_c,
      format: formatTemperature,
      rooms: benchmark.rooms_temperature,
    },
    {
      label: 'Humedad',
      roomValue: room.avg_humidity_pct,
      average: benchmark.avg_humidity_pct,
      format: formatHumidity,
      rooms: benchmark.rooms_humidity,
    },
    {
      label: 'CO₂',
      roomValue: room.avg_co2_ppm,
      average: benchmark.avg_co2_ppm,
      format: formatCo2,
      rooms: benchmark.rooms_co2,
      lowerIsBetter: true,
    },
    {
      label: 'Ocupación',
      roomValue: room.occupancy_pct,
      average: benchmark.occupancy_pct,
      format: formatOccupancy,
      rooms: benchmark.rooms_presence,
    },
  ];

  const visible = rows.filter((row) => row.roomValue !== null && row.average !== null);

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-3">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Comparación con la media
        </h3>
        <p className="text-xs text-muted-foreground">
          Media del resto de estancias con dato para el mismo periodo.
        </p>
      </div>

      {visible.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-500">
          No hay datos comparables para esta estancia.
        </p>
      ) : (
        <div className="space-y-3">
          {visible.map((row) => {
            const difference = (row.roomValue as number) - (row.average as number);
            const unit =
              row.label === 'Temperatura'
                ? '°C'
                : row.label === 'Humedad' || row.label === 'Ocupación'
                  ? 'pp'
                  : 'ppm';
            const isBetter = row.lowerIsBetter ? difference < 0 : Math.abs(difference) < 0.5;
            return (
              <div
                key={row.label}
                className="grid items-center gap-2 rounded-sm border border-slate-100 bg-slate-50/50 px-3 py-2 sm:grid-cols-[120px_1fr_1fr_100px]"
              >
                <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                  {row.label}
                </span>
                <span className="text-sm text-slate-800">
                  {row.format(row.roomValue)}
                  <span className="ml-2 text-[11px] text-slate-500">esta estancia</span>
                </span>
                <span className="text-sm text-slate-600">
                  {row.format(row.average)}
                  <span className="ml-2 text-[11px] text-slate-500">
                    media ({row.rooms})
                  </span>
                </span>
                <span
                  className={`text-sm font-semibold ${
                    row.lowerIsBetter
                      ? isBetter
                        ? 'text-success'
                        : 'text-orange-600'
                      : 'text-slate-700'
                  }`}
                >
                  {difference === 0 ? 'Igual' : deltaText(difference, unit)}
                </span>
              </div>
            );
          })}
        </div>
      )}
      <p className="mt-3 text-[11px] text-slate-500">
        {benchmark.rooms_presence > 0
          ? `La media de ocupación usa las otras ${benchmark.rooms_presence} estancias con presencia.`
          : 'Sin otras estancias con presencia para comparar.'}
      </p>
    </section>
  );
}
