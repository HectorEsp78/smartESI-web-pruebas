import { useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../ui/ChartCard';
import { RangeSelector } from '../ui/RangeSelector';
import { SelectField } from '../ui/SelectField';
import { StatCard } from '../ui/StatCard';
import { useBuildings } from '../../hooks/useBuildings';
import { useEnergyConsumption } from '../../hooks/useEnergyConsumption';
import { useGlobalRange } from '../../context/RangeContext';
import {
  ALL_BUILDINGS,
  DEFAULT_ENERGY_METRIC,
  ENERGY_METRICS,
  METRIC_LABEL,
} from '../../types/energy';
import type { EnergyMetric } from '../../types/energy';
import { METRIC_COLOR, AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  RANGE_LABEL,
  formatMetricValue,
  formatNumber,
  formatTimestamp,
} from '../../lib/format';

const METRIC_OPTIONS = ENERGY_METRICS.map((metric) => ({
  value: metric,
  label: METRIC_LABEL[metric],
}));

export function EnergyConsumptionChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const [metric, setMetric] = useState<EnergyMetric>(DEFAULT_ENERGY_METRIC);

  const { meta } = useBuildings();
  const { data, isLoading, isFetching, error, retry } = useEnergyConsumption(
    range,
    building,
    metric,
  );

  const copy = RANGE_FORMATTING[range];
  const color = METRIC_COLOR[metric];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];

  const isEmpty = !data || data.series.length === 0;

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
        ariaLabel="Métrica del consumo"
      />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label={`Consumo ${RANGE_LABEL[range].toLowerCase()}`}
          value={data ? formatMetricValue(data.total, data.unit) : '—'}
          hint={copy.title}
          tone="primary"
        />
        <StatCard
          label={`Media por ${data?.granularity === 'month' ? 'mes' : data?.granularity === 'day' ? 'día' : 'hora'}`}
          value={data ? formatMetricValue(data.average, data.unit) : '—'}
          hint={copy.subtitle}
        />
        <StatCard
          label="Pico"
          value={data?.peak ? formatMetricValue(data.peak.value, data.unit) : '—'}
          hint={data?.peak ? formatTimestamp(data.peak.timestamp, copy.tooltipPattern) : undefined}
          tone="accent"
        />
      </div>

      <ChartCard
        title={`${METRIC_LABEL[metric]} energético`}
        subtitle={`${copy.title} · ${copy.subtitle}`}
        unit={data?.unit}
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de consumo para el periodo seleccionado."
        onRetry={retry}
        height={340}
      >
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <AreaChart
            data={data?.series ?? []}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="energyAreaFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.35} />
                <stop offset="95%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => formatTimestamp(value as string, copy.tickPattern)}
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
              labelFormatter={(label) =>
                formatTimestamp(label as string, copy.tooltipPattern)
              }
              formatter={(value) => [
                formatMetricValue(Number(value), data?.unit ?? ''),
                METRIC_LABEL[metric],
              ]}
              contentStyle={TOOLTIP_STYLE}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill="url(#energyAreaFill)"
              activeDot={{ r: 4, strokeWidth: 0 }}
              isAnimationActive={!isFetching}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
