import { RangeSelector } from '../../ui/RangeSelector';
import {
  MAINTENANCE_DAYS_OPTIONS,
  maintenanceDaysLabel,
} from '../../../lib/maintenance';
import type { MaintenanceDays } from '../../../lib/maintenance';

interface MaintenanceFiltersProps {
  days: MaintenanceDays;
  onChange: (days: MaintenanceDays) => void;
}

const OPTIONS = MAINTENANCE_DAYS_OPTIONS.map((days) => ({
  value: String(days),
  label: `${days} días`,
}));

export function MaintenanceFilters({ days, onChange }: MaintenanceFiltersProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
          Periodo de análisis
        </span>
        <RangeSelector
          options={OPTIONS}
          value={String(days)}
          onChange={(value) => onChange(Number(value) as MaintenanceDays)}
          ariaLabel="Periodo de mantenimiento"
        />
      </div>
      <p className="pb-1 text-xs text-slate-500">
        {maintenanceDaysLabel(days)} · batería, transmisión y cortes
      </p>
    </div>
  );
}
