import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../../ui/ChartCard';
import { PartialMeterNote } from '../../ui/PartialMeterNote';
import { SelectField } from '../../ui/SelectField';
import { StatCard } from '../../ui/StatCard';
import { useBuildings } from '../../../hooks/useBuildings';
import { useEnergyBreakdown } from '../../../hooks/useEnergyStats';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatKwh,
  formatNumber,
  formatPercent,
  formatTimestamp,
} from '../../../lib/format';

const BASE_COLOR = '#94a3b8';
const ACTIVITY_COLOR = '#0497d7';
const LIGHTING_COLOR = '#cf6c2e';
const OTHER_COLOR = '#1f6f9a';

export function EnergyBreakdownChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useEnergyBreakdown(range, building);

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
          label="Consumo total"
          value={data ? formatKwh(data.total) : '—'}
          hint={copy.title}
          tone="primary"
        />
        <StatCard
          label="Carga base (fuera de horario)"
          value={data ? formatPercent(data.base_share * 100, 0) : '—'}
          hint={data ? `${formatKwh(data.base_total)} en noches y fines de semana` : undefined}
          tone="warning"
        />
        <StatCard
          label="Iluminación sobre el total"
          value={data ? formatPercent(data.lighting_share * 100, 0) : '—'}
          hint={data ? `${formatKwh(data.lighting_total)} atribuibles a luminarias` : undefined}
          tone="accent"
        />
      </div>

      {building !== ALL_BUILDINGS && <PartialMeterNote />}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard
          title="Carga base vs. actividad"
          subtitle={`${copy.title} · consumo fuera y dentro de horario`}
          unit="kWh"
          headerExtra={controls}
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <BarChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
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
                formatter={(value, name) => [formatKwh(Number(value)), String(name)]}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
              <Bar dataKey="activity" name="Actividad" stackId="a" fill={ACTIVITY_COLOR} />
              <Bar
                dataKey="base"
                name="Carga base"
                stackId="a"
                fill={BASE_COLOR}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Luz vs. resto de cargas"
          subtitle={`${copy.title} · reparto de la electricidad`}
          unit="kWh"
          isLoading={isLoading}
          error={error}
          isEmpty={isEmpty}
          emptyMessage="Sin datos para el periodo seleccionado."
          onRetry={retry}
          height={320}
        >
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <BarChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
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
                formatter={(value, name) => [formatKwh(Number(value)), String(name)]}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
              <Bar dataKey="other" name="Otras cargas" stackId="b" fill={OTHER_COLOR} />
              <Bar
                dataKey="lighting"
                name="Iluminación"
                stackId="b"
                fill={LIGHTING_COLOR}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
