import { useState } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '../../ui/ChartCard';
import { SelectField } from '../../ui/SelectField';
import { useBuildings } from '../../../hooks/useBuildings';
import { useValves } from '../../../hooks/useClimate';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, CHART_ACCENT, CHART_PRIMARY, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { RANGE_FORMATTING, formatNumber, formatPercent, formatTimestamp } from '../../../lib/format';
import type { ValveStatus } from '../../../types/climate';

const STATUS_LABEL: Record<ValveStatus, string> = {
  ok: 'Correcto',
  fria: 'Aula fría',
  valvula_abierta: 'Válvula abierta',
  valvula_cerrada: 'Válvula cerrada',
};

const STATUS_CLASS: Record<ValveStatus, string> = {
  ok: 'bg-success/10 text-success',
  fria: 'bg-warning/10 text-warning',
  valvula_abierta: 'bg-accent/10 text-accent',
  valvula_cerrada: 'bg-slate-200 text-slate-600',
};

export function ValvesTemperatureChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useValves(range, building);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const isEmpty = !data || data.series.length === 0;
  const setpoint = data?.setpoint_c ?? 21;

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
      <ChartCard
        title="Electroválvulas vs. temperatura de aula"
        subtitle={`${copy.title} · % de válvulas abiertas y temperatura media`}
        unit="°C"
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de válvulas para el periodo seleccionado."
        onRetry={retry}
        height={340}
      >
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <ComposedChart data={data?.series ?? []} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="valveFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_PRIMARY} stopOpacity={0.3} />
                <stop offset="95%" stopColor={CHART_PRIMARY} stopOpacity={0.02} />
              </linearGradient>
            </defs>
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
              domain={[0, 100]}
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={48}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[10, 30]}
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
                if (label === 'Válvulas abiertas') return [formatPercent(Number(value), 0), label];
                return [`${formatNumber(Number(value), 1)} °C`, label];
              }}
              contentStyle={TOOLTIP_STYLE}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="valve_open_pct"
              name="Válvulas abiertas"
              stroke={CHART_PRIMARY}
              strokeWidth={2}
              fill="url(#valveFill)"
            />
            <ReferenceLine
              yAxisId="right"
              y={setpoint}
              stroke="#b56a00"
              strokeDasharray="4 4"
              label={{ value: `Consigna ${setpoint}°C`, position: 'insideTopRight', fill: '#b56a00', fontSize: 11 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="avg_temperature"
              name="Temperatura media"
              stroke={CHART_ACCENT}
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      {data && data.spaces.length > 0 && (
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
          <h3 className="font-heading text-lg font-semibold text-slate-900">Estado por aula</h3>
          <p className="mb-3 text-xs text-muted-foreground">
            {copy.title} · compara la temperatura alcanzada con la consigna de {setpoint} °C
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 text-right font-semibold">T. media</th>
                  <th className="py-2 pr-4 text-right font-semibold">Desviación</th>
                  <th className="py-2 pr-4 text-right font-semibold">% válvula abierta</th>
                  <th className="py-2 pr-4 text-right font-semibold">Horas &lt; consigna</th>
                  <th className="py-2 text-right font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.avg_temperature, 1)} °C
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {space.deviation_c > 0 ? '+' : ''}
                      {formatNumber(space.deviation_c, 1)} °C
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatPercent(space.valve_open_pct, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.hours_below_setpoint, 0)}
                    </td>
                    <td className="py-2 text-right">
                      <span
                        className={`inline-block rounded-sm px-2 py-0.5 text-xs font-semibold ${STATUS_CLASS[space.status]}`}
                      >
                        {STATUS_LABEL[space.status]}
                      </span>
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
