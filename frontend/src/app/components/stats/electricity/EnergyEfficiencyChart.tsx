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
import { StatCard } from '../../ui/StatCard';
import { useEnergyEfficiency } from '../../../hooks/useEnergyStats';
import { useGlobalRange } from '../../../context/RangeContext';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE, buildingColor } from '../../../lib/chartTheme';
import {
  RANGE_FORMATTING,
  formatEuro,
  formatKwh,
  formatNumber,
  formatPercent,
} from '../../../lib/format';

export function EnergyEfficiencyChart() {
  const { range } = useGlobalRange();
  const { data, isLoading, error, retry } = useEnergyEfficiency(range);
  const copy = RANGE_FORMATTING[range];

  const topSpaces = (data?.spaces ?? []).slice(0, 10);
  const worst = data?.spaces[0] ?? null;
  const isEmpty = !data || data.spaces.length === 0;

  const exportRows = (data?.spaces ?? []).map((space) => [
    space.label,
    space.building_label,
    space.kind,
    space.area_m2,
    space.total,
    space.cost_eur,
    space.occupancy_hours,
    space.kwh_per_m2,
    space.kwh_per_person_hour,
  ]);

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
          label="Media por superficie"
          value={data ? `${formatNumber(data.avg_kwh_per_m2, 1)} kWh/m²` : '—'}
          hint="Referencia para detectar espacios ineficientes"
        />
        <StatCard
          label="Espacio menos eficiente"
          value={worst ? worst.label : '—'}
          hint={worst ? `${formatNumber(worst.kwh_per_m2, 1)} kWh/m²` : undefined}
          tone="accent"
        />
      </div>

      {data && data.coverage < 0.999 && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
          El consumo total procede del cuadro general. El detalle por edificio y espacio usa los
          subcontadores A/B, que cubren el {formatPercent(data.coverage * 100, 1)} del total; las
          intensidades por superficie son, por tanto, parciales.
        </p>
      )}

      <ChartCard
        title="Consumo por superficie (kWh/m²)"
        subtitle={`${copy.title} · espacios con mayor consumo por metro cuadrado`}
        unit="kWh/m²"
        headerExtra={
          <ExportCsvButton
            filename={`eficiencia-${range}.csv`}
            headers={[
              'Espacio',
              'Edificio',
              'Tipo',
              'Superficie m²',
              'Consumo kWh',
              'Coste €',
              'Horas-persona',
              'kWh/m²',
              'kWh/persona·hora',
            ]}
            rows={exportRows}
            disabled={!data}
          />
        }
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de eficiencia para el periodo seleccionado."
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
              formatter={(value, _name, item) => {
                const payload = item?.payload as { total?: number } | undefined;
                const total = payload?.total ?? 0;
                return [`${formatNumber(Number(value), 1)} kWh/m² (${formatKwh(total)})`, 'Intensidad'];
              }}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
            />
            <Bar dataKey="kwh_per_m2" radius={[0, 4, 4, 0]}>
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
            {copy.title} · consumo, superficie y normalización por ocupación
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Espacio</th>
                  <th className="py-2 pr-4 text-right font-semibold">kWh</th>
                  <th className="py-2 pr-4 text-right font-semibold">m²</th>
                  <th className="py-2 pr-4 text-right font-semibold">kWh/m²</th>
                  <th className="py-2 pr-4 text-right font-semibold">kWh/pers·h</th>
                  <th className="py-2 pr-4 text-right font-semibold">Coste</th>
                  <th className="py-2 text-right font-semibold">% total</th>
                </tr>
              </thead>
              <tbody>
                {data.spaces.map((space) => (
                  <tr key={space.space_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{space.label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.total, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.area_m2, 0)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatNumber(space.kwh_per_m2, 1)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatNumber(space.kwh_per_person_hour, 2)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-600">
                      {formatEuro(space.cost_eur)}
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
