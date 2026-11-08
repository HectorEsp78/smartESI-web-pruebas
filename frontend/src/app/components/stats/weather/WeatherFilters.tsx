import { RangeSelector } from '../../ui/RangeSelector';
import { WEATHER_DAYS_OPTIONS, weatherDaysLabel } from '../../../lib/weather';
import type { WeatherDays } from '../../../lib/weather';

interface WeatherFiltersProps {
  days: WeatherDays;
  onChange: (days: WeatherDays) => void;
}

const OPTIONS = WEATHER_DAYS_OPTIONS.map((days) => ({
  value: String(days),
  label: `${days} días`,
}));

export function WeatherFilters({ days, onChange }: WeatherFiltersProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
          Periodo de análisis
        </span>
        <RangeSelector
          options={OPTIONS}
          value={String(days)}
          onChange={(value) => onChange(Number(value) as WeatherDays)}
          ariaLabel="Periodo de medio ambiente"
        />
      </div>
      <p className="pb-1 text-xs text-slate-500">
        {weatherDaysLabel(days)} · estación meteorológica y cruces
      </p>
    </div>
  );
}
