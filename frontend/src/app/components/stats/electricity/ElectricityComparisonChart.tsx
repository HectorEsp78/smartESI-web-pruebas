import { useState } from 'react';
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
  formatElectricityValue,
  formatPeriod,
  isValidPeriod,
  metricLabel,
  previousYearPeriod,
  todayIso,
} from '../../../lib/electricity';
import { formatNumber, formatSignedPercent, formatTimestamp } from '../../../lib/format';
import {
  AXIS_LINE,
  AXIS_TICK,
  CHART_ACCENT,
  CHART_PRIMARY,
  TOOLTIP_STYLE,
} from '../../../lib/chartTheme';
import { useElectricityCompare } from '../../../hooks/useElectricity';
import type { ElectricityPeriod } from '../../../api/electricity';
import { ELECTRICITY_GRANULARITY_NOUN } from '../../../types/electricity';
import type {
  ElectricityCompareDto,
  ElectricityComparePointDto,
  ElectricityDto,
  ElectricityGranularity,
  ElectricityMetaDto,
  ElectricityMetric,
} from '../../../types/electricity';

interface ElectricityComparisonChartProps {
  mainPeriod: ElectricityPeriod;
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  building: string;
  sector: string;
  stats: ElectricityDto | null;
  meta: ElectricityMetaDto | null;
}

function PeriodFields({
  label,
  period,
  min,
  max,
  onChange,
  actionLabel,
  onAction,
}: {
  label: string;
  period: ElectricityPeriod;
  min?: string;
  max?: string;
  onChange: (period: ElectricityPeriod) => void;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="rounded-sm border border-slate-200 bg-slate-50/60 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-600">
          {label}
        </span>
        <button
          type="button"
          onClick={onAction}
          className="cursor-pointer text-[11px] font-semibold text-primary hover:underline"
        >
          {actionLabel}
        </button>
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

function ComparisonBody({ data }: { data: ElectricityCompareDto | null }) {
  if (!data) return null;
  const rows = data.series.map((point) => ({
    ...point,
    label: formatTimestamp(point.timestamp_a, ELECTRICITY_TICK_PATTERN[data.granularity]),
  }));
  const differentLength = data.period_a_days !== data.period_b_days;
  const positiveDelta = data.delta_pct > 0;
  const deltaLabel = formatSignedPercent(data.delta_pct, 1);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Periodo A"
          value={formatElectricityValue(data.period_a.total, data.unit)}
          hint={`${formatPeriod({ start: data.start_a, end: data.end_a })} (${data.period_a_days} días)`}
          tone="primary"
        />
        <StatCard
          label="Periodo B"
          value={formatElectricityValue(data.period_b.total, data.unit)}
          hint={`${formatPeriod({ start: data.start_b, end: data.end_b })} (${data.period_b_days} días)`}
        />
        <StatCard
          label="Variación A vs B"
          value={deltaLabel}
          hint="Diferencia del total del periodo A frente al B"
          tone={positiveDelta ? 'accent' : 'success'}
        />
        <StatCard
          label="Base media fuera de horario"
          value={`${formatElectricityValue(data.baseline_hourly, data.unit)}/h`}
          hint="Media de horas cerradas de ambos periodos"
          tone="warning"
        />
      </div>

      <ChartCard
        title="Comparativa de periodos"
        subtitle={`${data.scope_label} · ${metricLabel(data.metric)} por ${ELECTRICITY_GRANULARITY_NOUN[data.granularity]}; línea discontinua = base de centro cerrado`}
        unit={data.unit}
        isLoading={false}
        error={null}
        isEmpty={data.series.length === 0}
        emptyMessage="Sin datos para los dos periodos seleccionados."
        onRetry={() => undefined}
        height={340}
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
            <Tooltip
              labelFormatter={(_, payload) => {
                const point = payload?.[0]?.payload as ElectricityComparePointDto | undefined;
                if (!point) return '';
                return `${formatTimestamp(point.timestamp_a, ELECTRICITY_TOOLTIP_PATTERN[data.granularity])} · ${formatTimestamp(point.timestamp_b, ELECTRICITY_TOOLTIP_PATTERN[data.granularity])}`;
              }}
              formatter={(value, name) => [
                formatElectricityValue(Number(value), data.unit),
                String(name),
              ]}
              contentStyle={TOOLTIP_STYLE}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            <Line
              type="monotone"
              dataKey="period_a"
              name={`Periodo A · ${formatDateInputLabel(data.start_a)}`}
              stroke={CHART_PRIMARY}
              strokeWidth={2.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="period_b"
              name={`Periodo B · ${formatDateInputLabel(data.start_b)}`}
              stroke={CHART_ACCENT}
              strokeWidth={2.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="baseline"
              name="Base fuera de horario"
              stroke="#64748b"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          Periodo A: <strong className="text-slate-700">{formatPeriod({ start: data.start_a, end: data.end_a })}</strong>
        </span>
        <span>
          Periodo B: <strong className="text-slate-700">{formatPeriod({ start: data.start_b, end: data.end_b })}</strong>
        </span>
        <span>Los dos periodos deben tener el mismo número de intervalos.</span>
      </div>

      {differentLength && (
        <p className="rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Los periodos tienen distinta duración ({data.period_a_days} y {data.period_b_days} días).
          La comparación de totales es informativa; para una comparación estricta usa periodos de
          la misma duración.
        </p>
      )}
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
  const [periodA, setPeriodA] = useState<ElectricityPeriod>(mainPeriod);
  const [periodB, setPeriodB] = useState<ElectricityPeriod>(() => previousYearPeriod(mainPeriod));
  const valid = isValidPeriod(periodA) && isValidPeriod(periodB);
  const minDate = meta?.data_source === 'database' ? meta.data_start : undefined;
  const maxDate = todayIso();
  const beforeDataStart = Boolean(
    meta?.data_source === 'database' &&
      ((periodA.start && periodA.start < meta.data_start) ||
        (periodB.start && periodB.start < meta.data_start)),
  );
  const query = valid
    ? { periodA, periodB, granularity, metric, building, sector: sector || undefined }
    : null;
  const { data, isLoading, isFetching, error, retry } = useElectricityCompare(query);

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-white p-4 shadow-none">
        <div className="mb-3">
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Comparar dos periodos
          </h3>
          <p className="text-xs text-muted-foreground">
            Elige dos rangos independientes con el mismo número de intervalos. Se comparan en el
            mismo gráfico y se añade la base de centro cerrado.
          </p>
          {isFetching && query && (
            <p className="mt-1 text-xs font-semibold text-primary">Actualizando comparativa…</p>
          )}
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <PeriodFields
            label="Periodo A"
            period={periodA}
            min={minDate}
            max={maxDate}
            onChange={setPeriodA}
            actionLabel="Usar periodo principal"
            onAction={() => setPeriodA(mainPeriod)}
          />
          <PeriodFields
            label="Periodo B"
            period={periodB}
            min={minDate}
            max={maxDate}
            onChange={setPeriodB}
            actionLabel="Año anterior"
            onAction={() => setPeriodB(previousYearPeriod(periodA))}
          />
        </div>
        {!valid && (
          <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Revisa las fechas: la fecha final no puede ser anterior a la inicial.
          </p>
        )}
        {beforeDataStart && meta && (
          <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Los datos del recorder empiezan el {formatDateInputLabel(meta.data_start)}. Los periodos
            anteriores aparecerán sin datos.
          </p>
        )}
      </div>

      {!query ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-5 text-sm text-muted-foreground">
          Introduce dos periodos válidos para ver la comparativa.
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
      ) : (
        <ComparisonBody data={data} />
      )}

      {stats && (
        <p className="text-xs text-slate-500">
          La comparativa usa el ámbito seleccionado en los filtros: <strong>{stats.scope_label}</strong>.
        </p>
      )}
    </div>
  );
}
