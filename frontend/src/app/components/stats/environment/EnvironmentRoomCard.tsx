import type { ReactNode } from 'react';
import { ChevronRight, Droplets, Thermometer, Users } from 'lucide-react';
import { Link } from 'react-router';
import { formatHumidity, formatPresence, formatTemperature } from '../../../lib/environment';
import type { DatePeriod } from '../../../lib/electricity';
import type { EnvironmentRoomSummaryDto } from '../../../types/environment';
import { getRoomCardMetadata } from './roomCardMetadata';

interface EnvironmentRoomCardProps {
  room: EnvironmentRoomSummaryDto;
  period: DatePeriod;
}

interface MetricItemProps {
  icon: ReactNode;
  label: string;
  value: string;
  iconTone: string;
  valueColor: string;
}

function MetricItem({ icon, label, value, iconTone, valueColor }: MetricItemProps) {
  return (
    <div className="min-w-0 rounded-sm border border-slate-200/80 bg-white/85 px-1.5 py-1.5 shadow-[0_1px_0_rgba(15,23,42,0.03)] sm:px-2.5">
      <dt className="flex items-center justify-center gap-1.5 text-[0.64rem] font-bold uppercase tracking-[0.08em] text-slate-500 sm:justify-start">
        <span
          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-sm border sm:h-6 sm:w-6 ${iconTone}`}
        >
          {icon}
        </span>
        <span className="hidden sm:inline">{label}</span>
      </dt>
      <dd
        className={`mt-1 whitespace-nowrap text-center text-[0.72rem] font-bold tabular-nums min-[380px]:text-[0.8rem] sm:text-left sm:text-[0.95rem] ${valueColor}`}
      >
        {value}
      </dd>
    </div>
  );
}

function presenceBadge(room: EnvironmentRoomSummaryDto) {
  if (room.current_presence === true) {
    return {
      label: 'Con presencia',
      className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
      dotClassName: 'bg-emerald-500',
    };
  }
  if (room.current_presence === false) {
    return {
      label: 'Sin presencia',
      className: 'border-slate-200 bg-slate-50 text-slate-600',
      dotClassName: 'bg-slate-400',
    };
  }
  return {
    label: 'Sin dato',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
    dotClassName: 'bg-amber-500',
  };
}

export function EnvironmentRoomCard({ room, period }: EnvironmentRoomCardProps) {
  const metadata = getRoomCardMetadata(room.room_id);
  if (!metadata) return null;

  const badge = presenceBadge(room);
  const params = new URLSearchParams({ start: period.start, end: period.end });

  return (
    <Link
      to={`/infraestructura/${encodeURIComponent(room.room_id)}?${params.toString()}`}
      aria-label={`Ver detalle del aula ${metadata.technicalCode}`}
      className="group flex w-full flex-row overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_10px_30px_rgba(20,48,71,0.06)] transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-[0_18px_42px_rgba(20,48,71,0.12)] focus:outline-none focus:ring-2 focus:ring-primary/40"
    >
      <div className="relative w-28 shrink-0 overflow-hidden bg-primary sm:w-40 lg:w-44">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(4,151,215,0.98)_0%,rgba(4,151,215,0.84)_45%,rgba(20,48,71,0.96)_100%)]" />
        <img
          src={metadata.imageSrc}
          alt={metadata.imageAlt}
          className="absolute inset-0 h-full w-full object-cover grayscale mix-blend-luminosity contrast-125 transition-transform duration-700 ease-out group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(255,255,255,0.24),transparent_34%),linear-gradient(180deg,transparent_45%,rgba(9,25,42,0.42)_100%)]" />
      </div>

      <div className="flex min-w-0 flex-1 flex-col p-3 sm:p-4 sm:pb-5">
        <div className="flex items-start justify-between gap-2 sm:gap-3">
          <div className="min-w-0 font-room-card">
            <p className="text-[0.58rem] font-extrabold uppercase tracking-[0.16em] text-primary sm:text-[0.68rem] sm:tracking-[0.18em]">
              Aula
            </p>
            <h3 className="mt-1 flex items-center gap-1 text-lg font-extrabold uppercase leading-none tracking-[0.08em] text-slate-950 sm:gap-1.5 sm:text-xl">
              {metadata.technicalCode}
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:text-primary sm:h-4 sm:w-4" />
            </h3>
            <p className="mt-1.5 text-xs font-semibold leading-tight text-slate-700 sm:mt-2 sm:text-sm">
              {metadata.personName}
            </p>
          </div>

          <span
            className={`flex shrink-0 items-center gap-1 rounded-sm border px-1.5 py-0.5 text-[0.66rem] font-semibold sm:gap-1.5 sm:px-2.5 sm:py-1 sm:text-xs ${badge.className}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${badge.dotClassName}`} />
            {badge.label}
          </span>
        </div>

        <p className="mt-1.5 text-[0.68rem] text-muted-foreground sm:mt-2 sm:text-xs">
          {room.label}
        </p>

        <div className="my-2 h-px bg-slate-200 sm:my-3" />

        <dl className="grid grid-cols-3 gap-1.5 sm:gap-2">
          <MetricItem
            icon={<Thermometer className="h-3.5 w-3.5 text-orange-500" strokeWidth={2.5} />}
            label="Temp."
            value={formatTemperature(room.current_temperature_c)}
            iconTone="border-orange-100 bg-orange-50"
            valueColor="text-orange-600"
          />
          <MetricItem
            icon={<Droplets className="h-3.5 w-3.5 text-blue-500" strokeWidth={2.5} />}
            label="Humedad"
            value={formatHumidity(room.current_humidity_pct)}
            iconTone="border-blue-100 bg-blue-50"
            valueColor="text-blue-600"
          />
          <MetricItem
            icon={
              <Users
                className={`h-3.5 w-3.5 ${
                  room.current_presence ? 'text-emerald-500' : 'text-slate-500'
                }`}
                strokeWidth={2.5}
              />
            }
            label="Presencia"
            value={formatPresence(room.current_presence)}
            iconTone={
              room.current_presence
                ? 'border-emerald-100 bg-emerald-50'
                : 'border-slate-200 bg-slate-50'
            }
            valueColor={room.current_presence ? 'text-emerald-600' : 'text-slate-700'}
          />
        </dl>
      </div>
    </Link>
  );
}
