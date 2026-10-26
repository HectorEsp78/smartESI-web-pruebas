import { RangeSelector } from '../../ui/RangeSelector';
import { SelectField } from '../../ui/SelectField';
import { formatDateInputLabel, isValidPeriod, todayIso } from '../../../lib/electricity';
import { formatNumber } from '../../../lib/format';
import {
  ELECTRICITY_ALL,
  ELECTRICITY_METRIC_LABEL,
  ELECTRICITY_METRICS,
} from '../../../types/electricity';
import type { ElectricityMetaDto, ElectricityMetric } from '../../../types/electricity';

interface ElectricityFiltersProps {
  meta: ElectricityMetaDto | null;
  start: string;
  end: string;
  metric: ElectricityMetric;
  building: string;
  sector: string;
  onStartChange: (value: string) => void;
  onEndChange: (value: string) => void;
  onMetricChange: (value: ElectricityMetric) => void;
  onBuildingChange: (value: string) => void;
  onSectorChange: (value: string) => void;
}

const METRIC_OPTIONS = ELECTRICITY_METRICS.map((metric) => ({
  value: metric,
  label: ELECTRICITY_METRIC_LABEL[metric],
}));

function DateInput({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: string;
  min?: string;
  max?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="inline-flex flex-col gap-1 text-xs text-slate-600">
      <span className="font-semibold uppercase tracking-[0.08em]">{label}</span>
      <input
        type="date"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-sm border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
      />
    </label>
  );
}

export function ElectricityFilters({
  meta,
  start,
  end,
  metric,
  building,
  sector,
  onStartChange,
  onEndChange,
  onMetricChange,
  onBuildingChange,
  onSectorChange,
}: ElectricityFiltersProps) {
  const period = { start, end };
  const validPeriod = isValidPeriod(period);
  const buildingOptions = [
    { value: ELECTRICITY_ALL, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const sectorOptions = [
    { value: '', label: 'Todos los sectores medidos' },
    ...(meta?.sectors ?? [])
      .filter((item) => item.available && item.building_id === 'FerminCaballero')
      .map((item) => ({ value: item.id, label: item.label })),
  ];
  const unavailableSectors = (meta?.sectors ?? []).filter(
    (item) => !item.available && item.building_id === 'FerminCaballero',
  );
  // The recorder start date only constrains real data; mock mode generates
  // synthetic series for any date the user picks.
  const isDatabase = meta?.data_source === 'database';
  const minDate = isDatabase ? meta?.data_start : undefined;
  const beforeDataStart = Boolean(isDatabase && meta && start && start < meta.data_start);

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-none">
      <div className="flex flex-wrap items-end gap-4">
        <DateInput
          label="Desde"
          value={start}
          min={minDate}
          max={todayIso()}
          onChange={onStartChange}
        />
        <DateInput
          label="Hasta"
          value={end}
          min={minDate}
          max={todayIso()}
          onChange={onEndChange}
        />

        <SelectField
          label="Edificio"
          value={building}
          onChange={onBuildingChange}
          options={buildingOptions}
        />

        {building === 'FerminCaballero' && (
          <SelectField
            label="Sector"
            value={sector}
            onChange={onSectorChange}
            options={sectorOptions}
          />
        )}

        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-600">
            Ver
          </span>
          <RangeSelector
            options={METRIC_OPTIONS}
            value={metric}
            onChange={onMetricChange}
            ariaLabel="Ver consumo o coste"
          />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          Periodo: <strong className="text-slate-700">{formatDateInputLabel(start)}</strong> –{' '}
          <strong className="text-slate-700">{formatDateInputLabel(end)}</strong>
        </span>
        {metric === 'cost' && meta && (
          <span>Precio aplicado: {formatNumber(meta.price_eur_per_kwh, 2)} €/kWh</span>
        )}
        {building !== 'FerminCaballero' && building !== 'all' && (
          <span>Este edificio solo tiene contador total; no hay desglose por cuadros.</span>
        )}
        {unavailableSectors.length > 0 && (
          <span>
            Sin datos: {unavailableSectors.map((item) => item.label).join(', ')}.
          </span>
        )}
      </div>

      {!validPeriod && (
        <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          La fecha final no puede ser anterior a la fecha inicial.
        </p>
      )}
      {beforeDataStart && meta && (
        <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Los datos del recorder empiezan el {formatDateInputLabel(meta.data_start)}. Las fechas
          anteriores aparecerán sin datos.
        </p>
      )}
    </div>
  );
}
