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
import { PartialMeterNote } from '../../ui/PartialMeterNote';
import { RangeSelector } from '../../ui/RangeSelector';
import { SelectField } from '../../ui/SelectField';
import { StatCard } from '../../ui/StatCard';
import { useBuildings } from '../../../hooks/useBuildings';
import { useEnergyCompare } from '../../../hooks/useEnergyStats';
import { useGlobalRange } from '../../../context/RangeContext';
import {
  ALL_BUILDINGS,
  DEFAULT_ENERGY_METRIC,
  ENERGY_METRICS,
  METRIC_LABEL,
} from '../../../types/energy';
import type { EnergyMetric } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, CHART_ACCENT, CHART_PRIMARY, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatMetricValue,
  formatNumber,
  formatSignedPercent,
  formatTimestamp,
} from '../../../lib/format';

const METRIC_OPTIONS = ENERGY_METRICS.map((metric) => ({
  value: metric,
  label: METRIC_LABEL[metric],
}));

export function EnergyCompareChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const [metric, setMetric] = useState<EnergyMetric>(DEFAULT_ENERGY_METRIC);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useEnergyCompare(range, building, metric);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const isEmpty = !data || data.series.length === 0;
  const isUp = (data?.delta_pct ?? 0) > 0;

  const controls = (
    <div className="flex flex-wrap items-center gap-3">
      <SelectField
        label="Edificio"
        value={building}
        onChange={setBuilding}
        options={buildingOptions}
      />
      <RangeSelector
        options={METRIC_OPTIONS}
        value={metric}
        onChange={setMetric}
        ariaLabel="Métrica de la comparativa"
      />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Periodo actual"
          value={data ? formatMetricValue(data.current_total, data.unit) : '—'}
          hint={copy.title}
          tone="primary"
        />
        <StatCard
          label="Periodo anterior"
          value={data ? formatMetricValue(data.previous_total, data.unit) : '—'}
          hint="Mismo intervalo, un periodo antes"
        />
        <StatCard
          label="Variación"
          value={data ? formatSignedPercent(data.delta_pct, 1) : '—'}
          hint={isUp ? 'El consumo ha subido' : 'El consumo ha bajado'}
          tone={isUp ? 'accent' : 'success'}
        />
      </div>

      {building !== ALL_BUILDINGS && <PartialMeterNote />}

      <ChartCard
        title="Comparativa con el periodo anterior"
        subtitle={`${copy.title} · actual frente al periodo equivalente anterior`}
        unit={data?.unit}
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos para la comparativa del periodo seleccionado."
        onRetry={retry}
        height={340}
      >
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <LineChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => formatTimestamp(value as string, copy.tickPattern)}
              minTickGap={24}
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
              labelFormatter={(label) => formatTimestamp(label as string, copy.tooltipPattern)}
              formatter={(value, name) => [
                formatMetricValue(Number(value), data?.unit ?? ''),
                String(name),
              ]}
              contentStyle={TOOLTIP_STYLE}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            <Line
              type="monotone"
              dataKey="current"
              name="Actual"
              stroke={CHART_PRIMARY}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="previous"
              name="Anterior"
              stroke={CHART_ACCENT}
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
