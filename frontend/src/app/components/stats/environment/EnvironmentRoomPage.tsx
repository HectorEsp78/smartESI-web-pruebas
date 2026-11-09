import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { ArrowLeft, Droplets, Thermometer, Users } from 'lucide-react';
import {
  EnvironmentRoomHumidityChart,
  EnvironmentRoomPresenceChart,
  EnvironmentRoomTemperatureChart,
} from './EnvironmentRoomCharts';
import { EnvironmentRangeSelector } from './EnvironmentRangeSelector';
import { getRoomCardMetadata } from './roomCardMetadata';
import { useEnvironmentRoom } from '../../../hooks/useEnvironment';
import { useEnvironmentPeriod } from '../../../hooks/useEnvironmentPeriod';
import {
  environmentPeriodError,
  formatEnvironmentPeriod,
  formatHumidity,
  formatPresence,
  formatTemperature,
} from '../../../lib/environment';
import type { DatePeriod } from '../../../lib/electricity';
import type {
  EnvironmentGranularity,
  EnvironmentRoomSummaryDto,
} from '../../../types/environment';

interface EnvironmentRoomPageProps {
  roomId: string;
}

function indexHref(period: DatePeriod): string {
  const params = new URLSearchParams({ start: period.start, end: period.end });
  return `/infraestructura?${params.toString()}`;
}

function granularityLabel(granularity: EnvironmentGranularity): string {
  if (granularity === 'hour') return 'Agregación horaria';
  if (granularity === 'day') return 'Agregación diaria';
  return 'Agregación semanal';
}

function presenceTone(value: boolean | null): string {
  if (value === true) return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (value === false) return 'border-slate-200 bg-slate-50 text-slate-600';
  return 'border-amber-200 bg-amber-50 text-amber-800';
}

function CurrentMetric({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div className={`rounded-md border px-3 py-2 ${tone}`}>
      <p className="flex items-center gap-1.5 text-[0.68rem] font-bold uppercase tracking-[0.08em]">
        {icon}
        {label}
      </p>
      <p className="mt-1 text-lg font-bold tabular-nums">{value}</p>
    </div>
  );
}

function RoomHeader({ room, period }: { room: EnvironmentRoomSummaryDto; period: DatePeriod }) {
  const metadata = getRoomCardMetadata(room.room_id);

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_10px_30px_rgba(20,48,71,0.06)]">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          {metadata && (
            <div className="relative hidden h-24 w-32 shrink-0 overflow-hidden rounded-md bg-primary sm:block">
              <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(4,151,215,0.9)_0%,rgba(20,48,71,0.9)_100%)]" />
              <img
                src={metadata.imageSrc}
                alt={metadata.imageAlt}
                className="absolute inset-0 h-full w-full object-cover grayscale mix-blend-luminosity contrast-125"
              />
            </div>
          )}
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Aula</p>
            <h2 className="font-heading text-2xl font-extrabold uppercase tracking-[0.06em] text-slate-950">
              {metadata?.technicalCode ?? room.room_id}
            </h2>
            <p className="mt-1 text-sm font-semibold text-slate-700">
              {metadata?.personName ?? room.label}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {room.building_label} · {formatEnvironmentPeriod(period)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 sm:min-w-[320px]">
          <CurrentMetric
            icon={<Thermometer className="h-3.5 w-3.5" />}
            label="Temp."
            value={formatTemperature(room.current_temperature_c)}
            tone="border-orange-200 bg-orange-50 text-orange-800"
          />
          <CurrentMetric
            icon={<Droplets className="h-3.5 w-3.5" />}
            label="Humedad"
            value={formatHumidity(room.current_humidity_pct)}
            tone="border-blue-200 bg-blue-50 text-blue-800"
          />
          <CurrentMetric
            icon={<Users className="h-3.5 w-3.5" />}
            label="Presencia"
            value={formatPresence(room.current_presence)}
            tone={presenceTone(room.current_presence)}
          />
        </div>
      </div>
    </section>
  );
}

export function EnvironmentRoomPage({ roomId }: EnvironmentRoomPageProps) {
  const { period, setPeriod } = useEnvironmentPeriod();
  const periodError = environmentPeriodError(period);
  const queryPeriod = periodError ? null : period;
  const { data, isLoading, error, retry } = useEnvironmentRoom(roomId, queryPeriod);

  return (
    <div className="mt-5 space-y-5">
      <Link
        to={indexHref(period)}
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary transition-colors hover:text-primary/80"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver a las aulas
      </Link>

      {data && !periodError && !error && <RoomHeader room={data.room} period={period} />}

      {/* Always visible: it is the way out of an invalid period or a failed load. */}
      <EnvironmentRangeSelector period={period} onChange={setPeriod} />

      {periodError ? (
        <div className="rounded-md border border-dashed border-amber-300 bg-amber-50 p-6 text-sm text-amber-900">
          {periodError} Elige otro periodo para cargar el aula.
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-6">
          <p className="font-semibold text-destructive">No se pudo cargar el aula.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            Reintentar
          </button>
        </div>
      ) : !data || isLoading ? (
        <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white py-20">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <h3 className="font-heading text-lg font-semibold text-slate-900">
              Evolución en el periodo
            </h3>
            <p className="text-xs text-muted-foreground">{granularityLabel(data.granularity)}</p>
          </div>

          <EnvironmentRoomTemperatureChart series={data.series} granularity={data.granularity} />
          <EnvironmentRoomHumidityChart series={data.series} granularity={data.granularity} />
          <EnvironmentRoomPresenceChart series={data.series} granularity={data.granularity} />
        </div>
      )}
    </div>
  );
}
