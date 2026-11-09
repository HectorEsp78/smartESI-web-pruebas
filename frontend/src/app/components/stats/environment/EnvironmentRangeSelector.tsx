import { defaultElectricityPeriod } from '../../../lib/electricity';
import type { DatePeriod } from '../../../lib/electricity';
import { formatEnvironmentPeriod } from '../../../lib/environment';

interface EnvironmentRangeSelectorProps {
  period: DatePeriod;
  onChange: (period: DatePeriod) => void;
}

const RANGE_OPTIONS: ReadonlyArray<{ label: string; days: number }> = [
  { label: 'Día', days: 1 },
  { label: 'Semana', days: 7 },
  { label: 'Mes', days: 30 },
];

export function EnvironmentRangeSelector({ period, onChange }: EnvironmentRangeSelectorProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
      <div>
        <p className="font-heading text-sm font-semibold text-slate-900">Periodo</p>
        <p className="text-xs text-muted-foreground">{formatEnvironmentPeriod(period)}</p>
      </div>
      <div
        className="flex flex-wrap items-center gap-1.5 sm:gap-2"
        role="group"
        aria-label="Periodo de las gráficas"
      >
        {RANGE_OPTIONS.map((option) => {
          const optionPeriod = defaultElectricityPeriod(option.days);
          // Compare the dates, not the length: seven days of last month are
          // not the "last week" this button selects.
          const isActive = optionPeriod.start === period.start && optionPeriod.end === period.end;
          return (
            <button
              key={option.days}
              type="button"
              onClick={() => onChange(optionPeriod)}
              aria-pressed={isActive}
              className={`cursor-pointer rounded-sm border px-3 py-1.5 text-xs transition-colors sm:px-4 ${
                isActive
                  ? 'border-primary bg-primary font-semibold text-primary-foreground'
                  : 'border-slate-300 bg-white text-slate-700 hover:border-primary hover:text-primary'
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
