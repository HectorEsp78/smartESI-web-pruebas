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
import { ChartCard } from '../../ui/ChartCard';
import { SelectField } from '../../ui/SelectField';
import { StatCard } from '../../ui/StatCard';
import { useBuildings } from '../../../hooks/useBuildings';
import { useLightingWaste } from '../../../hooks/useLighting';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE, buildingColor } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatEuro,
  formatKwh,
  formatNumber,
  formatPercent,
} from '../../../lib/format';

export function LightingWasteChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useLightingWaste(range, building);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const topSpaces = (data?.spaces ?? []).slice(0, 12);
  const isEmpty = !data || data.spaces.length === 0;

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
          label="Luz encendida sin ocupación"
          value={data ? formatKwh(data.waste_lighting) : '—'}
          hint={copy.title}
          tone="accent"
        />
        <StatCard
          label="Peso sobre la iluminación"
          value={data ? formatPercent(data.waste_share * 100, 0) : '—'}
          hint={data ? `${formatKwh(data.total_lighting)} de luminarias en total` : undefined}
        />
        <StatCard
          label="Ahorro estimado al año"
          value={data ? formatEuro(data.annualized_cost_eur) : '—'}
          hint={data ? `${formatEuro(data.waste_cost_eur)} en el periodo` : undefined}
          tone="success"
        />
      </div>

      <ChartCard
        title="Despilfarro por espacio"
        subtitle={`${copy.title} · kWh de luminarias encendidas con el espacio vacío`}
        unit="kWh"
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de despilfarro para el periodo seleccionado."
        onRetry={retry}
        height={380}
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
              formatter={(value) => [formatKwh(Number(value)), 'Sin ocupación']}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(179, 1, 57, 0.08)' }}
            />
            <Bar dataKey="empty_lighting" fill="#b30139" radius={[0, 4, 4, 0]}>
              {topSpaces.map((space, index) => (
                <Cell key={space.space_id} fill={buildingColor(space.building_id, index)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {data && !isEmpty && (
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Detalle por espacio
          </h3>
          <p className="mb-3 text-xs text-muted-foreground">
            {copy.title} · horas vacías y ahorro anualizado estimado
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 text-right font-semibold">Luz total</th>
                  <th className="py-2 pr-4 text-right font-semibold">Sin ocupación</th>
                  <th className="py-2 pr-4 text-right font-semibold">% despilfarro</th>
                  <th className="py-2 pr-4 text-right font-semibold">Horas vacío</th>
                  <th className="py-2 text-right font-semibold">€ / año</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.total_lighting, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.empty_lighting, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatPercent(space.waste_pct * 100, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.empty_hours, 0)}
                    </td>
                    <td className="py-2 text-right tabular-nums font-semibold text-accent">
                      {formatEuro(space.annualized_cost_eur)}
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
