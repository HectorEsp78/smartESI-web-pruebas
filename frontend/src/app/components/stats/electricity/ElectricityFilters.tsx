import { DateInput } from '../../ui/DateInput';
import { RangeSelector } from '../../ui/RangeSelector';
import { SelectField } from '../../ui/SelectField';
import { formatDateInputLabel, isValidPeriod, todayIso } from '../../../lib/electricity';
import { formatNumber } from '../../../lib/format';
import {
  ELECTRICITY_ALL,
  ELECTRICITY_METRIC_LABEL,
  ELECTRICITY_METRICS,
  FERMIN_BUILDING_ID,
} from '../../../types/electricity';
import type { ElectricityMetaDto, ElectricityMetric } from '../../../types/electricity';

interface ElectricityFiltersProps {
  meta: ElectricityMetaDto | null;
  start: string;
  end: string;
  metric: ElectricityMetric;
  building: string;
  sector: string;
  /** Effective tariff of the selected period, when the API has measured it. */
  priceEurPerKwh?: number | null;
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

export function ElectricityFilters({
  meta,
  start,
  end,
  metric,
  building,
  sector,
  priceEurPerKwh,
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
      .filter((item) => item.available && item.building_id === FERMIN_BUILDING_ID)
      .map((item) => ({ value: item.id, label: item.label })),
  ];
  const unavailableSectors = (meta?.sectors ?? []).filter(
    (item) => !item.available && item.building_id === FERMIN_BUILDING_ID,
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

        {building === FERMIN_BUILDING_ID && (
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
          <span>
            Precio aplicado:{' '}
            {formatNumber(priceEurPerKwh ?? meta.price_eur_per_kwh, 3)} €/kWh
          </span>
        )}
        {building !== FERMIN_BUILDING_ID && building !== ELECTRICITY_ALL && (
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
