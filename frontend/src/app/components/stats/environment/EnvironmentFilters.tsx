import { periodDays, todayIso } from '../../../lib/electricity';
import type { DatePeriod } from '../../../lib/electricity';
import {
  MAX_ENVIRONMENT_DAYS,
  environmentPeriodError,
} from '../../../lib/environment';

interface EnvironmentFiltersProps {
  period: DatePeriod;
  onChange: (period: DatePeriod) => void;
}

function DateInput({
  label,
  value,
  max,
  onChange,
}: {
  label: string;
  value: string;
  max: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="inline-flex flex-col gap-1 text-xs text-slate-600">
      <span className="font-semibold uppercase tracking-[0.08em] text-slate-500">{label}</span>
      <input
        type="date"
        value={value}
        max={max}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-sm border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
      />
    </label>
  );
}

export function EnvironmentFilters({ period, onChange }: EnvironmentFiltersProps) {
  const error = environmentPeriodError(period);
  const days = periodDays(period);
  const max = todayIso();

  return (
    <div className="flex flex-wrap items-end justify-between gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="flex flex-wrap items-end gap-3">
        <DateInput
          label="Desde"
          value={period.start}
          max={max}
          onChange={(start) => onChange({ ...period, start })}
        />
        <DateInput
          label="Hasta"
          value={period.end}
          max={max}
          onChange={(end) => onChange({ ...period, end })}
        />
      </div>
      <p className="pb-1 text-xs text-slate-500">
        {error ? (
          <span className="font-semibold text-destructive">{error}</span>
        ) : (
          <>
            {days} {days === 1 ? 'día' : 'días'} · máximo {MAX_ENVIRONMENT_DAYS}
          </>
        )}
      </p>
    </div>
  );
}
