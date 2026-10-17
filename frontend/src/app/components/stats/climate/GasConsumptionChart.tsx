import { useState } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../../ui/ChartCard';
import { SelectField } from '../../ui/SelectField';
import { StatCard } from '../../ui/StatCard';
import { useBuildings } from '../../../hooks/useBuildings';
import { useGas } from '../../../hooks/useClimate';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, CHART_ACCENT, CHART_PRIMARY, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatEuro,
  formatKwh,
  formatNumber,
  formatTimestamp,
} from '../../../lib/format';

const GAS_COLOR = '#cf6c2e';
const DEGREE_COLOR = '#1f6f9a';

function correlationHint(r: number): string {
  const abs = Math.abs(r);
  const strength = abs >= 0.7 ? 'fuerte' : abs >= 0.4 ? 'moderada' : 'débil';
  return `Relación ${strength} con el frío`;
}

export function GasConsumptionChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useGas(range, building);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const isEmpty = !data || data.series.length === 0;
  const stats = data?.stats;

  const controls = (
    <SelectField
      label="Edificio"
      value={building}
      onChange={setBuilding}
      options={buildingOptions}
    />
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Gas consumido"
          value={data ? formatKwh(stats?.total_gas ?? 0) : '—'}
          hint={copy.title}
          tone="accent"
        />
        <StatCard
          label="Coste del gas"
          value={stats ? formatEuro(stats.cost_eur) : '—'}
          hint={stats ? `${formatNumber(stats.co2_kg, 0)} kg CO₂` : undefined}
        />
        <StatCard
          label="Relación con los grados-día"
          value={stats ? formatNumber(stats.correlation_degree_days, 2) : '—'}
          hint={stats ? correlationHint(stats.correlation_degree_days) : undefined}
          tone="primary"
        />
        <StatCard
          label="Gas por grado-día"
          value={stats ? `${formatNumber(stats.gas_per_degree_day, 1)} kWh` : '—'}
          hint={stats ? `${formatNumber(stats.total_degree_days, 0)} grados-día acumulados` : undefined}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Gas y grados-día"
          subtitle={`${copy.title} · el gas sigue al frío exterior`}
          unit="kWh"
          headerExtra={controls}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos de gas para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <ComposedChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
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
                yAxisId="left"
                tickFormatter={(value) => formatNumber(Number(value), 0)}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={60}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(value) => formatNumber(Number(value), 1)}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={48}
              />
              <Tooltip
                labelFormatter={(label) => formatTimestamp(label as string, copy.tooltipPattern)}
                formatter={(value, name) => {
                  const label = String(name);
                  if (label === 'Grados-día') return [formatNumber(Number(value), 1), label];
                  return [formatKwh(Number(value)), label];
                }}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: 'rgba(207, 108, 46, 0.10)' }}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
              <Bar yAxisId="left" dataKey="gas" name="Gas" fill={GAS_COLOR} radius={[4, 4, 0, 0]} />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="degree_days"
                name="Grados-día"
                stroke={DEGREE_COLOR}
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Temperatura interior y exterior"
          subtitle={`${copy.title} · media por intervalo`}
          unit="°C"
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos de temperatura para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <ComposedChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
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
                width={48}
              />
              <Tooltip
                labelFormatter={(label) => formatTimestamp(label as string, copy.tooltipPattern)}
                formatter={(value, name) => [`${formatNumber(Number(value), 1)} °C`, String(name)]}
                contentStyle={TOOLTIP_STYLE}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
              <Line
                type="monotone"
                dataKey="indoor_temperature"
                name="Interior"
                stroke={CHART_PRIMARY}
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="outdoor_temperature"
                name="Exterior"
                stroke={CHART_ACCENT}
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
