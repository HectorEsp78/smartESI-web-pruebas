import { useState } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../ui/ChartCard';
import { SelectField } from '../ui/SelectField';
import { StatCard } from '../ui/StatCard';
import { useBuildings } from '../../hooks/useBuildings';
import { useOccupancyAirQuality } from '../../hooks/useOccupancyAirQuality';
import { useGlobalRange } from '../../context/RangeContext';
import { ALL_BUILDINGS } from '../../types/energy';
import {
  AXIS_LINE,
  AXIS_TICK,
  CHART_ACCENT,
  CHART_PRIMARY,
  TOOLTIP_STYLE,
  buildingColor,
} from '../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatNumber,
  formatPercent,
  formatTimestamp,
} from '../../lib/format';

const CO2_GOOD_MAX = 800;
const CO2_MODERATE_MAX = 1200;

function correlationHint(r: number): string {
  const abs = Math.abs(r);
  const strength = abs >= 0.7 ? 'fuerte' : abs >= 0.4 ? 'moderada' : 'débil';
  const sign = r >= 0 ? 'positiva' : 'negativa';
  return `Correlación ${strength} ${sign}`;
}

export function OccupancyAirQualityChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);

  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useOccupancyAirQuality(range, building);

  const copy = RANGE_FORMATTING[range];
  const color = buildingColor(building, 0);
  const points = data?.points ?? [];
  const isEmpty = points.length === 0;

  const occupancyValues = points.map((point) => point.occupancy);
  const minOccupancy = occupancyValues.length ? Math.min(...occupancyValues) : 0;
  const maxOccupancy = occupancyValues.length ? Math.max(...occupancyValues) : 0;
  type SegmentPoint = { x: number; y: number };
  const regression: [SegmentPoint, SegmentPoint] | null = data
    ? [
        {
          x: minOccupancy,
          y: data.stats.slope * minOccupancy + data.stats.intercept,
        },
        {
          x: maxOccupancy,
          y: data.stats.slope * maxOccupancy + data.stats.intercept,
        },
      ]
    : null;

  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];

  const controls = (
    <div className="flex flex-wrap items-center gap-3">
      <SelectField
        label="Edificio"
        value={building}
        onChange={setBuilding}
        options={buildingOptions}
      />
    </div>
  );

  const stats = data?.stats;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Correlación ocupación–CO₂"
          value={stats ? formatNumber(stats.pearson_r, 2) : '—'}
          hint={stats ? correlationHint(stats.pearson_r) : undefined}
          tone="primary"
        />
        <StatCard
          label="CO₂ medio"
          value={stats ? `${formatNumber(stats.avg_co2, 0)} ppm` : '—'}
          hint={stats ? `Máx. ${formatNumber(stats.max_co2, 0)} ppm` : undefined}
        />
        <StatCard
          label="Aire bueno"
          value={stats ? formatPercent(stats.good_pct, 0) : '—'}
          hint="Tiempo por debajo de 800 ppm"
          tone="success"
        />
        <StatCard
          label="Ocupación media"
          value={stats ? formatPercent(stats.avg_occupancy_pct, 0) : '—'}
          hint={stats ? `${formatNumber(stats.avg_occupancy, 0)} personas de media` : undefined}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Ocupación vs. CO₂"
          subtitle={`${copy.title} · cada punto es un intervalo`}
          unit="ppm"
          headerExtra={controls}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                dataKey="occupancy"
                name="Ocupación"
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
              />
              <YAxis
                type="number"
                dataKey="co2"
                name="CO₂ (ppm)"
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={56}
              />
              <ReferenceLine y={CO2_GOOD_MAX} stroke="#b56a00" strokeDasharray="4 4" />
              <ReferenceLine y={CO2_MODERATE_MAX} stroke="#d4183d" strokeDasharray="4 4" />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value, name) => {
                  const label = String(name);
                  const unit = label === 'Ocupación' ? ' personas' : ' ppm';
                  return [`${formatNumber(Number(value), 0)}${unit}`, label];
                }}
                cursor={{ strokeDasharray: '3 3' }}
              />
              <Scatter name="Muestras" data={points} fill={color} fillOpacity={0.7} />
              {regression && (
                <ReferenceLine
                  segment={regression}
                  stroke={CHART_PRIMARY}
                  strokeWidth={2}
                  strokeDasharray="6 4"
                />
              )}
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Evolución conjunta"
          subtitle={`${copy.title} · ocupación y CO₂ en el tiempo`}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <ComposedChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="occupancyFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_PRIMARY} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CHART_PRIMARY} stopOpacity={0.02} />
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
                yAxisId="left"
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={48}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={56}
              />
              <Tooltip
                labelFormatter={(label) =>
                  formatTimestamp(label as string, copy.tooltipPattern)
                }
                formatter={(value, name) => {
                  const label = String(name);
                  const unit = label === 'Ocupación' ? ' personas' : ' ppm';
                  return [`${formatNumber(Number(value), 0)}${unit}`, label];
                }}
                contentStyle={TOOLTIP_STYLE}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
              <ReferenceLine
                yAxisId="right"
                y={CO2_GOOD_MAX}
                stroke="#b56a00"
                strokeDasharray="4 4"
              />
              <ReferenceLine
                yAxisId="right"
                y={CO2_MODERATE_MAX}
                stroke="#d4183d"
                strokeDasharray="4 4"
              />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="occupancy"
                name="Ocupación"
                stroke={CHART_PRIMARY}
                strokeWidth={2}
                fill="url(#occupancyFill)"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="co2"
                name="CO₂ (ppm)"
                stroke={CHART_ACCENT}
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
