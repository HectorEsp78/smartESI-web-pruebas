import { useEffect, useRef, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../../ui/ChartCard';
import { StatCard } from '../../ui/StatCard';
import {
  ELECTRICITY_TICK_PATTERN,
  ELECTRICITY_TOOLTIP_PATTERN,
  formatDateInputLabel,
  formatDayCount,
  formatElectricityValue,
  formatPeriod,
  isValidPeriod,
  metricLabel,
  previousYearPeriod,
  suggestComparisonPeriod,
  todayIso,
} from '../../../lib/electricity';
import { formatNumber, formatSignedPercent, formatTimestamp } from '../../../lib/format';
import {
  AXIS_LINE,
  AXIS_TICK,
  TOOLTIP_STYLE,
  comparisonColor,
} from '../../../lib/chartTheme';
import { useElectricityCompareMany } from '../../../hooks/useElectricity';
import type { ElectricityPeriod } from '../../../api/electricity';
import { ELECTRICITY_GRANULARITY_NOUN } from '../../../types/electricity';
import type {
  ElectricityCompareManyDto,
  ElectricityComparePeriodDto,
  ElectricityDto,
  ElectricityGranularity,
  ElectricityMetaDto,
  ElectricityMetric,
} from '../../../types/electricity';

const MAX_COMPARISON_PERIODS = 12;

interface ElectricityComparisonChartProps {
  mainPeriod: ElectricityPeriod;
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  building: string;
  sector: string;
  stats: ElectricityDto | null;
  meta: ElectricityMetaDto | null;
}

interface ComparisonRow {
  index: number;
  label: string;
  timestamps: Array<string | null>;
  values: Array<number | null>;
  baseline: number;
  [key: string]: unknown;
}

function PeriodFields({
  index,
  period,
  min,
  max,
  color,
  isReference,
  canRemove,
  onChange,
  onUseMain,
  onRemove,
}: {
  index: number;
  period: ElectricityPeriod;
  min?: string;
  max?: string;
  color: string;
  isReference: boolean;
  canRemove: boolean;
  onChange: (period: ElectricityPeriod) => void;
  onUseMain: () => void;
  onRemove: () => void;
}) {
  return (
    <div className="rounded-sm border border-slate-200 bg-slate-50/60 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-slate-600">
          <span
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          Periodo {index + 1}
          {isReference && (
            <span className="rounded-sm bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold normal-case tracking-normal text-primary">
              Referencia
            </span>
          )}
        </span>
        <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold">
          {isReference && (
            <button
              type="button"
              onClick={onUseMain}
              className="cursor-pointer text-primary hover:underline"
            >
              Usar periodo principal
            </button>
          )}
          <button
            type="button"
            onClick={() => onChange(previousYearPeriod(period))}
            className="cursor-pointer text-primary hover:underline"
          >
            Año anterior
          </button>
          {canRemove && (
            <button
              type="button"
              onClick={onRemove}
              className="cursor-pointer text-accent hover:underline"
            >
              Quitar
            </button>
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <label className="inline-flex flex-col gap-1 text-[11px] text-slate-500">
          <span>Desde</span>
          <input
            type="date"
            value={period.start}
            min={min}
            max={max}
            onChange={(event) => onChange({ ...period, start: event.target.value })}
            className="rounded-sm border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </label>
        <label className="inline-flex flex-col gap-1 text-[11px] text-slate-500">
          <span>Hasta</span>
          <input
            type="date"
            value={period.end}
            min={min}
            max={max}
            onChange={(event) => onChange({ ...period, end: event.target.value })}
            className="rounded-sm border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </label>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">{formatPeriod(period)}</p>
    </div>
  );
}

function ComparisonTooltip({
  active,
  payload,
  data,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ComparisonRow }>;
  data: ElectricityCompareManyDto;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;

  const pattern = ELECTRICITY_TOOLTIP_PATTERN[data.granularity];
  const firstTimestamp = row.timestamps.find(
    (value): value is string => typeof value === 'string' && value.length > 0,
  );

  return (
    <div style={TOOLTIP_STYLE} className="min-w-[250px] p-3">
      <p className="mb-2 text-xs font-semibold text-slate-700">
        {firstTimestamp
          ? formatTimestamp(firstTimestamp, pattern)
          : `Intervalo ${row.index + 1}`}
      </p>
      <ul className="space-y-1.5">
        {data.periods.map((period, index) => {
          const value = row.values[index] ?? null;
          const timestamp = row.timestamps[index];
          return (
            <li
              key={`${period.start}-${period.end}-${index}`}
              className="flex items-start justify-between gap-4 text-xs"
            >
              <span className="flex items-start gap-2 text-slate-600">
                <span
                  className="mt-1 h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: comparisonColor(index) }}
                  aria-hidden="true"
                />
                <span>
                  <span className="font-semibold text-slate-800">Periodo {index + 1}</span>
                  <span className="block text-[10px] text-slate-500">
                    {timestamp
                      ? formatTimestamp(timestamp, pattern)
                      : 'Sin datos en este intervalo'}
                  </span>
                </span>
              </span>
              <span className="shrink-0 font-semibold text-slate-900">
                {value == null ? '—' : formatElectricityValue(value, data.unit)}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-2 border-t border-slate-100 pt-2 text-[11px] text-slate-500">
        Base fuera de horario:{' '}
        <strong className="text-slate-700">
          {formatElectricityValue(row.baseline, data.unit)}
        </strong>
      </p>
    </div>
  );
}

function ComparisonTable({ data }: { data: ElectricityCompareManyDto }) {
  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr className="text-left text-[11px] uppercase tracking-[0.08em] text-slate-500">
            <th className="px-3 py-2 font-semibold">Periodo</th>
            <th className="px-3 py-2 font-semibold">Rango</th>
            <th className="px-3 py-2 text-right font-semibold">Duración</th>
            <th className="px-3 py-2 text-right font-semibold">Total</th>
            <th className="px-3 py-2 text-right font-semibold">Variación vs P1</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {data.periods.map((period: ElectricityComparePeriodDto, index) => {
            const isReference = index === 0;
            const deltaClass = isReference
              ? 'text-slate-400'
              : period.delta_pct > 0
                ? 'text-accent'
                : period.delta_pct < 0
                  ? 'text-success'
                  : 'text-slate-600';
            return (
              <tr key={`${period.start}-${period.end}-${index}`}>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <span className="inline-flex items-center gap-2 font-semibold text-slate-800">
                    <span
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: comparisonColor(index) }}
                      aria-hidden="true"
                    />
                    Periodo {index + 1}
                  </span>
                  {isReference && (
                    <span className="ml-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                      Referencia
                    </span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-slate-600">
                  {formatPeriod({ start: period.start, end: period.end })}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-right text-slate-600">
                  {formatDayCount(period.days)}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-right font-semibold text-slate-900">
                  {formatElectricityValue(period.stats.total, data.unit)}
                </td>
                <td className={`whitespace-nowrap px-3 py-2.5 text-right font-semibold ${deltaClass}`}>
                  {isReference ? '—' : formatSignedPercent(period.delta_pct, 1)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="border-t border-slate-100 px-3 py-2 text-[11px] text-slate-500">
        La variación compara cada periodo con el periodo 1. En consumo y coste, un valor positivo
        indica un gasto mayor.
      </p>
    </div>
  );
}

function ComparisonBody({ data }: { data: ElectricityCompareManyDto }) {
  const reference = data.periods[0];
  const tickPattern = ELECTRICITY_TICK_PATTERN[data.granularity];
  const rows: ComparisonRow[] = data.series.map((point) => {
    const firstTimestamp = point.timestamps.find(
      (value): value is string => typeof value === 'string' && value.length > 0,
    );
    const row: ComparisonRow = {
      index: point.index,
      label: firstTimestamp
        ? formatTimestamp(firstTimestamp, tickPattern)
        : String(point.index + 1),
      timestamps: point.timestamps,
      values: point.values,
      baseline: point.baseline,
    };
    point.values.forEach((value, index) => {
      row[`period_${index}`] = value;
    });
    return row;
  });

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard
          label="Periodo de referencia"
          value={formatElectricityValue(reference.stats.total, data.unit)}
          hint={`${formatPeriod({ start: reference.start, end: reference.end })} (${formatDayCount(reference.days)})`}
          tone="primary"
        />
        <StatCard
          label="Base media fuera de horario"
          value={`${formatElectricityValue(data.baseline_hourly, data.unit)}/h`}
          hint="Media de horas cerradas de todos los periodos"
          tone="warning"
        />
        <StatCard
          label="Periodos comparados"
          value={String(data.periods.length)}
          hint={
            data.equal_length
              ? 'Todos tienen la misma duración'
              : 'Duraciones distintas: se alinean desde el inicio'
          }
          tone={data.equal_length ? 'success' : 'neutral'}
        />
      </div>

      <ComparisonTable data={data} />

      <ChartCard
        title="Comparativa de periodos"
        subtitle={`${data.scope_label} · ${metricLabel(data.metric)} por ${ELECTRICITY_GRANULARITY_NOUN[data.granularity]}; línea discontinua = base de centro cerrado`}
        unit={data.unit}
        isLoading={false}
        error={null}
        isEmpty={data.series.length === 0}
        emptyMessage="Sin datos para los periodos seleccionados."
        onRetry={() => undefined}
        height={data.periods.length > 4 ? 400 : 340}
      >
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="label"
              minTickGap={28}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
            />
            <YAxis
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={64}
            />
            <Tooltip content={<ComparisonTooltip data={data} />} />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            {data.periods.map((period, index) => (
              <Line
                key={`${period.start}-${period.end}-${index}`}
                type="monotone"
                dataKey={`period_${index}`}
                name={`P${index + 1} · ${formatDateInputLabel(period.start)}`}
                stroke={comparisonColor(index)}
                strokeWidth={2.5}
                dot={false}
                connectNulls={false}
              />
            ))}
            <Line
              type="monotone"
              dataKey="baseline"
              name="Base fuera de horario"
              stroke="#64748b"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {!data.equal_length && (
        <p className="rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Los periodos no tienen la misma duración ({data.periods.map((period) => formatDayCount(period.days)).join(', ')}).
          La gráfica los alinea desde su fecha inicial y deja vacíos los intervalos que no existen;
          la comparación de totales es informativa.
        </p>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          Periodos: <strong className="text-slate-700">{data.periods.length}</strong>
        </span>
        <span>
          Referencia: <strong className="text-slate-700">Periodo 1</strong>
        </span>
        <span>Los intervalos se alinean desde el inicio de cada periodo.</span>
      </div>
    </div>
  );
}

export function ElectricityComparisonChart({
  mainPeriod,
  granularity,
  metric,
  building,
  sector,
  stats,
  meta,
}: ElectricityComparisonChartProps) {
  const [periods, setPeriods] = useState<ElectricityPeriod[]>(() => [
    mainPeriod,
    previousYearPeriod(mainPeriod),
  ]);
  const previousMainPeriod = useRef(mainPeriod);

  // Keep the reference period in sync with the main filters while it has not
  // been customised. This avoids showing an old comparison after changing the
  // dates at the top of the tab.
  useEffect(() => {
    const previous = previousMainPeriod.current;
    previousMainPeriod.current = mainPeriod;
    if (previous.start === mainPeriod.start && previous.end === mainPeriod.end) return;
    setPeriods((current) =>
      current.map((period, index) =>
        index === 0 && period.start === previous.start && period.end === previous.end
          ? mainPeriod
          : period,
      ),
    );
  }, [mainPeriod]);

  const validPeriods = periods.filter(isValidPeriod);
  const valid = periods.length >= 2 && validPeriods.length === periods.length;
  const duplicatePeriods =
    new Set(validPeriods.map((period) => `${period.start}|${period.end}`)).size !==
    validPeriods.length;
  const minDate = meta?.data_source === 'database' ? meta.data_start : undefined;
  const maxDate = todayIso();
  const beforeDataStart = Boolean(
    meta?.data_source === 'database' &&
      periods.some((period) => period.start && period.start < meta.data_start),
  );
  const query = valid
    ? { periods, granularity, metric, building, sector: sector || undefined }
    : null;
  const { data, isLoading, isFetching, error, retry } = useElectricityCompareMany(query);
  const canAdd = periods.length < MAX_COMPARISON_PERIODS;

  const updatePeriod = (index: number, value: ElectricityPeriod) => {
    setPeriods((current) =>
      current.map((period, periodIndex) => (periodIndex === index ? value : period)),
    );
  };

  const removePeriod = (index: number) => {
    setPeriods((current) =>
      current.length <= 2 ? current : current.filter((_, periodIndex) => periodIndex !== index),
    );
  };

  const addPeriod = () => {
    setPeriods((current) =>
      current.length >= MAX_COMPARISON_PERIODS
        ? current
        : [...current, suggestComparisonPeriod(current, mainPeriod)],
    );
  };

  const resetPeriods = () => {
    setPeriods([mainPeriod, previousYearPeriod(mainPeriod)]);
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-white p-4 shadow-none">
        <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-heading text-lg font-semibold text-slate-900">
              Comparar periodos
            </h3>
            <p className="text-xs text-muted-foreground">
              Añade hasta {MAX_COMPARISON_PERIODS} periodos y compáralos en la misma gráfica. Cada
              periodo tiene sus propias fechas y la variación se calcula frente al periodo 1.
            </p>
            {isFetching && query && (
              <p className="mt-1 text-xs font-semibold text-primary">Actualizando comparativa…</p>
            )}
          </div>
          <button
            type="button"
            onClick={resetPeriods}
            className="cursor-pointer rounded-sm border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:border-primary hover:text-primary"
          >
            Restablecer
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {periods.map((period, index) => (
            <PeriodFields
              key={`period-${index}`}
              index={index}
              period={period}
              min={minDate}
              max={maxDate}
              color={comparisonColor(index)}
              isReference={index === 0}
              canRemove={periods.length > 2}
              onChange={(value) => updatePeriod(index, value)}
              onUseMain={() => updatePeriod(index, mainPeriod)}
              onRemove={() => removePeriod(index)}
            />
          ))}

          {canAdd && (
            <button
              type="button"
              onClick={addPeriod}
              className="flex min-h-[148px] cursor-pointer flex-col items-center justify-center rounded-sm border border-dashed border-slate-300 bg-white p-3 text-sm font-semibold text-primary transition-colors hover:border-primary hover:bg-primary/5"
            >
              <span className="text-lg leading-none">+</span>
              <span className="mt-1">Añadir periodo</span>
              <span className="mt-1 text-[11px] font-normal text-slate-500">
                Se propone el mismo rango un año antes
              </span>
            </button>
          )}
        </div>

        {!valid && (
          <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Revisa las fechas: necesitas al menos dos periodos y la fecha final no puede ser
            anterior a la inicial.
          </p>
        )}
        {duplicatePeriods && (
          <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Hay periodos con las mismas fechas. Puedes compararlos, pero la gráfica mostrará líneas
            superpuestas.
          </p>
        )}
        {beforeDataStart && meta && (
          <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Los datos del recorder empiezan el {formatDateInputLabel(meta.data_start)}. Los periodos
            anteriores aparecerán sin datos.
          </p>
        )}
        {!canAdd && (
          <p className="mt-3 text-xs text-slate-500">
            Has alcanzado el máximo de {MAX_COMPARISON_PERIODS} periodos por comparativa.
          </p>
        )}
      </div>

      {!query ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-5 text-sm text-muted-foreground">
          Introduce al menos dos periodos válidos para ver la comparativa.
        </div>
      ) : isLoading ? (
        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex h-[340px] items-center justify-center">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-5">
          <p className="font-semibold text-destructive">No se pudo cargar la comparativa.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Reintentar
          </button>
        </div>
      ) : data ? (
        <ComparisonBody data={data} />
      ) : null}

      {stats && (
        <p className="text-xs text-slate-500">
          La comparativa usa el ámbito seleccionado en los filtros: <strong>{stats.scope_label}</strong>.
        </p>
      )}
    </div>
  );
}
