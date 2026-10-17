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
import { useLightingConsumption } from '../../../hooks/useLighting';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatEuro,
  formatKwh,
  formatNumber,
  formatPercent,
  formatTimestamp,
} from '../../../lib/format';

const LIGHTING_COLOR = '#cf6c2e';
const OTHER_COLOR = '#1f6f9a';
const DAYLIGHT_COLOR = '#b56a00';

export function LightingConsumptionChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useLightingConsumption(range, building);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const isEmpty = !data || data.series.length === 0;

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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Consumo de luminarias"
          value={data ? formatKwh(data.lighting_total) : '—'}
          hint={copy.title}
          tone="accent"
        />
        <StatCard
          label="Peso sobre la electricidad"
          value={data ? formatPercent(data.lighting_share * 100, 0) : '—'}
          hint={data ? `${formatKwh(data.total)} de consumo total` : undefined}
          tone="primary"
        />
        <StatCard
          label="Coste de la iluminación"
          value={data ? formatEuro(data.cost_eur) : '—'}
          hint={data ? `${formatNumber(data.co2_kg, 0)} kg CO₂` : undefined}
        />
      </div>

      <ChartCard
        title="Iluminación frente a la luz natural"
        subtitle={`${copy.title} · kWh de luminarias y horas de luz del día`}
        unit="kWh"
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de iluminación para el periodo seleccionado."
        onRetry={retry}
        height={340}
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
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={48}
            />
            <Tooltip
              labelFormatter={(label) => formatTimestamp(label as string, copy.tooltipPattern)}
              formatter={(value, name) => {
                const label = String(name);
                if (label === 'Luz natural') return [`${formatNumber(Number(value), 1)} h`, label];
                return [formatKwh(Number(value)), label];
              }}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            <Bar yAxisId="left" dataKey="other" name="Otras cargas" stackId="e" fill={OTHER_COLOR} />
            <Bar
              yAxisId="left"
              dataKey="lighting"
              name="Iluminación"
              stackId="e"
              fill={LIGHTING_COLOR}
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="daylight_hours"
              name="Luz natural"
              stroke={DAYLIGHT_COLOR}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
