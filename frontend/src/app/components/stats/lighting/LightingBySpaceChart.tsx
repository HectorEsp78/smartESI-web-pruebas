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
import { ExportCsvButton } from '../../ui/ExportCsvButton';
import { SelectField } from '../../ui/SelectField';
import { useBuildings } from '../../../hooks/useBuildings';
import { useLightingBySpace } from '../../../hooks/useLighting';
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

export function LightingBySpaceChart() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useLightingBySpace(range, building);

  const copy = RANGE_FORMATTING[range];
  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];
  const topSpaces = (data?.spaces ?? []).slice(0, 10);
  const isEmpty = !data || data.spaces.length === 0;

  const exportRows = (data?.spaces ?? []).map((space) => [
    space.label,
    space.building_label,
    space.kind,
    space.area_m2,
    space.lighting,
    space.share_of_lighting,
    space.share_of_building,
    space.cost_eur,
  ]);

  const controls = (
    <div className="flex flex-wrap items-end gap-3">
      <SelectField
        label="Edificio"
        value={building}
        onChange={setBuilding}
        options={buildingOptions}
      />
      <ExportCsvButton
        filename={`iluminacion-espacios-${range}-${building}.csv`}
        headers={[
          'Espacio',
          'Edificio',
          'Tipo',
          'Superficie m²',
          'Iluminación kWh',
          'Cuota de iluminación',
          'Cuota del edificio',
          'Coste €',
        ]}
        rows={exportRows}
        disabled={!data}
      />
    </div>
  );

  return (
    <div className="space-y-4">
      <ChartCard
        title="Luminarias por espacio"
        subtitle={`${copy.title} · espacios con mayor consumo de iluminación`}
        unit="kWh"
        headerExtra={controls}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de iluminación para el periodo seleccionado."
        onRetry={retry}
        height={360}
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
              formatter={(value) => [formatKwh(Number(value)), 'Iluminación']}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
            />
            <Bar dataKey="lighting" radius={[0, 4, 4, 0]}>
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
            {copy.title} · consumo de luminarias y peso sobre el total del edificio
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 font-semibold">Edificio</th>
                  <th className="py-2 pr-4 text-right font-semibold">kWh luz</th>
                  <th className="py-2 pr-4 text-right font-semibold">% luz</th>
                  <th className="py-2 pr-4 text-right font-semibold">% del edificio</th>
                  <th className="py-2 text-right font-semibold">Coste</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-slate-600">{space.building_label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.lighting, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatPercent(space.share_of_lighting * 100, 1)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatPercent(space.share_of_building * 100, 1)}
                    </td>
                    <td className="py-2 text-right tabular-nums text-slate-600">
                      {formatEuro(space.cost_eur)}
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
