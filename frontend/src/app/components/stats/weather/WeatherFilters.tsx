import { DateInput } from '../../ui/DateInput';
import { defaultElectricityPeriod, todayIso } from '../../../lib/electricity';
import type { DatePeriod } from '../../../lib/electricity';
import { WEATHER_PERIOD_SHORTCUTS } from '../../../lib/weather';

interface WeatherFiltersProps {
  period: DatePeriod;
  error: string | null;
  onChange: (period: DatePeriod) => void;
}

export function WeatherFilters({ period, error, onChange }: WeatherFiltersProps) {
  const today = todayIso();

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-end gap-4">
        <DateInput
          label="Desde"
          value={period.start}
          max={today}
          onChange={(start) => onChange({ ...period, start })}
        />
        <DateInput
          label="Hasta"
          value={period.end}
          max={today}
          onChange={(end) => onChange({ ...period, end })}
        />
        <div
          className="flex flex-wrap items-center gap-1.5"
          role="group"
          aria-label="Periodos rápidos"
        >
          {WEATHER_PERIOD_SHORTCUTS.map((days) => {
            const shortcut = defaultElectricityPeriod(days);
            const isActive = shortcut.start === period.start && shortcut.end === period.end;
            return (
              <button
                key={days}
                type="button"
                onClick={() => onChange(shortcut)}
                aria-pressed={isActive}
                className={`cursor-pointer rounded-sm border px-3 py-1.5 text-xs transition-colors ${
                  isActive
                    ? 'border-primary bg-primary font-semibold text-primary-foreground'
                    : 'border-slate-300 bg-white text-slate-700 hover:border-primary hover:text-primary'
                }`}
              >
                {days} días
              </button>
            );
          })}
        </div>
      </div>
      {error && (
        <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          {error}
        </p>
      )}
    </div>
  );
}
