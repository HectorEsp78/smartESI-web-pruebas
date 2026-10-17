import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../ui/ChartCard';
import { RangeSelector } from '../ui/RangeSelector';
import { useEnergyByBuilding } from '../../hooks/useEnergyByBuilding';
import { useGlobalRange } from '../../context/RangeContext';
import {
  DEFAULT_ENERGY_METRIC,
  ENERGY_METRICS,
  METRIC_LABEL,
} from '../../types/energy';
import type { EnergyMetric } from '../../types/energy';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE, buildingColor } from '../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatMetricValue,
  formatNumber,
  formatPercent,
} from '../../lib/format';

const METRIC_OPTIONS = ENERGY_METRICS.map((metric) => ({
  value: metric,
  label: METRIC_LABEL[metric],
}));

function shortLabel(label: string): string {
  return label.replace(/^Edificio\s+/i, '');
}

export function EnergyByBuildingChart() {
  const { range } = useGlobalRange();
  const [metric, setMetric] = useState<EnergyMetric>(DEFAULT_ENERGY_METRIC);

  const { data, isLoading, error, retry } = useEnergyByBuilding(range, metric);
  const copy = RANGE_FORMATTING[range];

  const buildings = (data?.buildings ?? []).map((building) => ({
    ...building,
    short: shortLabel(building.label),
  }));
  const topSpaces = (data?.spaces ?? []).slice(0, 8);
  const isEmpty = !data || data.buildings.length === 0;

  const controls = (
    <div className="flex flex-wrap items-center gap-3">
      <RangeSelector
        options={METRIC_OPTIONS}
        value={metric}
        onChange={setMetric}
        ariaLabel="Métrica del consumo por edificio"
      />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Consumo por edificio"
          subtitle={`${copy.title} · reparto entre edificios`}
          unit={data?.unit}
          headerExtra={controls}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos de edificios para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <BarChart data={buildings} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="short"
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                interval={0}
              />
              <YAxis
                tickFormatter={(value) => formatNumber(Number(value), 0)}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={64}
              />
              <Tooltip
                formatter={(value) => [
                  formatMetricValue(Number(value), data?.unit ?? ''),
                  METRIC_LABEL[metric],
                ]}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
              />
              <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                {buildings.map((building, index) => (
                  <Cell key={building.building_id} fill={buildingColor(building.building_id, index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Top espacios por consumo"
          subtitle={`${copy.title} · 8 espacios con mayor consumo`}
          unit={data?.unit}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos de espacios para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <BarChart
              data={topSpaces}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 8, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={(value) => formatNumber(Number(value), 0)}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={150}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
              />
              <Tooltip
                formatter={(value) => [
                  formatMetricValue(Number(value), data?.unit ?? ''),
                  METRIC_LABEL[metric],
                ]}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
              />
              <Bar dataKey="total" radius={[0, 4, 4, 0]}>
                {topSpaces.map((space, index) => (
                  <Cell key={space.space_id} fill={buildingColor(space.building_id, index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {data && !isEmpty && (
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Detalle por espacio
          </h3>
          <p className="mb-3 text-xs text-muted-foreground">
            {copy.title} · consumo y porcentaje sobre el total ({formatMetricValue(data.total, data.unit)})
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 font-semibold">Edificio</th>
                  <th className="py-2 pr-4 text-right font-semibold">Consumo</th>
                  <th className="py-2 text-right font-semibold">% total</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-slate-600">{space.building_label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatMetricValue(space.total, data.unit)}
                    </td>
                    <td className="py-2 text-right tabular-nums text-slate-600">
                      {formatPercent(space.share * 100, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
