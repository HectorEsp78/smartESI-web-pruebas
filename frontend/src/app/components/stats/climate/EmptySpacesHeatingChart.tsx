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
import { useEmptySpaces } from '../../../hooks/useClimate';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE, buildingColor } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatEuro,
  formatKwh,
  formatNumber,
} from '../../../lib/format';

export function EmptySpacesHeatingChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useEmptySpaces(range, building);

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
          label="Gas en espacios vacíos"
          value={data ? formatKwh(data.total_gas_estimate) : '—'}
          hint={copy.title}
          tone="accent"
        />
        <StatCard
          label="Horas de calefacción sin ocupación"
          value={data ? `${formatNumber(data.total_heated_unoccupied_hours, 0)} h` : '—'}
          hint={data ? `Base ${formatNumber(data.heat_base_temperature_c, 0)} °C` : undefined}
        />
        <StatCard
          label="Coste estimado anual"
          value={data ? formatEuro(data.total_annualized_cost_eur) : '—'}
          hint={data ? `${formatEuro(data.total_cost_eur)} en el periodo` : undefined}
          tone="warning"
        />
      </div>

      <ChartCard
        title="Calefacción de espacios vacíos"
        subtitle={`${copy.title} · gas estimado consumido sin ocupación`}
        unit="kWh"
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de calefacción para el periodo seleccionado."
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
              formatter={(value) => [formatKwh(Number(value)), 'Gas sin ocupación']}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(207, 108, 46, 0.10)' }}
            />
            <Bar dataKey="gas_estimate" radius={[0, 4, 4, 0]}>
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
            {copy.title} · temperatura media sin ocupación y ahorro anualizado estimado
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 font-semibold">Edificio</th>
                  <th className="py-2 pr-4 text-right font-semibold">T. sin ocupación</th>
                  <th className="py-2 pr-4 text-right font-semibold">Horas calentando</th>
                  <th className="py-2 pr-4 text-right font-semibold">Gas</th>
                  <th className="py-2 text-right font-semibold">€ / año</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-slate-600">{space.building_label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.avg_temperature_unoccupied, 1)} °C
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.heated_unoccupied_hours, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.gas_estimate, 0)}
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
