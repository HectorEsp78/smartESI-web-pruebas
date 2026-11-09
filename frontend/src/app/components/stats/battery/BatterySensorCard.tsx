import { formatTimestamp } from '../../../lib/format';
import { BATTERY_LEVEL_LABEL, batteryBarPct, formatBatteryValue } from '../../../lib/battery';
import { formatAge } from '../../../lib/weather';
import type { BatteryLevel, BatterySensorDto } from '../../../types/battery';

const BADGE_CLASS: Record<BatteryLevel, string> = {
  ok: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  medium: 'border-sky-200 bg-sky-50 text-sky-800',
  low: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-700',
  unknown: 'border-slate-300 bg-slate-100 text-slate-700',
};

const BAR_CLASS: Record<BatteryLevel, string> = {
  ok: 'bg-emerald-600',
  medium: 'bg-sky-600',
  low: 'bg-amber-500',
  critical: 'bg-red-600',
  unknown: 'bg-slate-400',
};

interface BatterySensorCardProps {
  sensor: BatterySensorDto;
  onSelect: (sensor: BatterySensorDto) => void;
}

function readingText(sensor: BatterySensorDto): string {
  if (!sensor.reading_at) return 'Nunca ha enviado una lectura válida';
  const when = formatTimestamp(sensor.reading_at, 'd MMM yyyy, HH:mm');
  return `${sensor.is_current ? 'Lectura' : 'Última lectura'}: ${when} (hace ${formatAge(sensor.age_hours)})`;
}

export function BatterySensorCard({ sensor, onSelect }: BatterySensorCardProps) {
  const isVoltage = sensor.unit === 'millivolt';

  return (
    <button
      type="button"
      onClick={() => onSelect(sensor)}
      aria-haspopup="dialog"
      className="flex w-full cursor-pointer flex-col rounded-md border border-slate-200 bg-white p-4 text-left transition-colors hover:border-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
    >
      <span className="flex items-start justify-between gap-2">
        <span className="font-heading text-sm font-semibold text-slate-900">{sensor.label}</span>
        <span
          className={`shrink-0 rounded-sm border px-2 py-0.5 text-xs font-semibold ${BADGE_CLASS[sensor.level]}`}
        >
          {BATTERY_LEVEL_LABEL[sensor.level]}
        </span>
      </span>

      <span className="mt-3 font-heading text-3xl font-bold text-slate-900">
        {formatBatteryValue(sensor.value, sensor.unit)}
      </span>
      {isVoltage && (
        <span className="text-xs text-slate-600">
          {sensor.estimated_pct === null ? 'Sin estimación' : `≈ ${sensor.estimated_pct} % estimado`}
        </span>
      )}

      <span className="mt-3 block h-1.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
        <span
          className={`block h-full rounded-full ${BAR_CLASS[sensor.level]}`}
          style={{ width: `${batteryBarPct(sensor)}%` }}
        />
      </span>

      <span className="mt-3 text-xs text-slate-500">{readingText(sensor)}</span>
      <span className="mt-1 text-xs font-semibold text-primary">Ver histórico</span>
    </button>
  );
}
