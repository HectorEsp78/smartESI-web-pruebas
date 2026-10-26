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
import { ExportCsvButton } from '../../ui/ExportCsvButton';
import { formatNumber, formatPercent, formatTimestamp } from '../../../lib/format';
import {
  ELECTRICITY_TICK_PATTERN,
  ELECTRICITY_TOOLTIP_PATTERN,
  formatElectricityValue,
  metricLabel,
} from '../../../lib/electricity';
import {
  AXIS_LINE,
  AXIS_TICK,
  ELECTRICITY_BUILDING_COLORS,
  TOOLTIP_STYLE,
  buildingColor,
} from '../../../lib/chartTheme';
import { ELECTRICITY_GRANULARITY_NOUN } from '../../../types/electricity';
import type { ElectricityDto } from '../../../types/electricity';

interface ElectricityBuildingsChartProps {
  data: ElectricityDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function ElectricityBuildingsChart({
  data,
  isLoading,
  isFetching,
  error,
  retry,
}: ElectricityBuildingsChartProps) {
  const granularity = data?.granularity ?? 'day';
  const noun = ELECTRICITY_GRANULARITY_NOUN[granularity];
  const unit = data?.unit ?? 'kWh';
  const rows = (data?.series ?? []).map((point, index) => {
    // The chart always stacks the three buildings, so its reference line must
    // be the whole-site baseline (sum of the three building baselines), not
    // the baseline of whichever scope is selected in the filters.
    const row: Record<string, string | number> = { timestamp: point.timestamp };
    let siteBaseline = 0;
    for (const building of data?.buildings ?? []) {
      row[building.building_id] = building.series[index]?.value ?? 0;
      siteBaseline += building.series[index]?.baseline ?? 0;
    }
    row.baseline = siteBaseline;
    return row;
  });
  const isEmpty = !data || data.series.length === 0;
  const tableRows = (data?.buildings ?? []).map((building) => [
    building.label,
    building.total,
    building.average,
    building.minimum,
    building.maximum,
    Number((building.share * 100).toFixed(1)),
  ]);

  return (
    <div className="space-y-4">
      <ChartCard
        title="Reparto por edificio"
        subtitle={`${metricLabel(data?.metric ?? 'kwh')} por ${noun} · barras apiladas y base de centro cerrado`}
        unit={data?.unit}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de edificios para el periodo seleccionado."
        onRetry={retry}
        height={340}
      >
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <ComposedChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) =>
                formatTimestamp(value as string, ELECTRICITY_TICK_PATTERN[granularity])
              }
              minTickGap={28}
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
              labelFormatter={(label) =>
                formatTimestamp(label as string, ELECTRICITY_TOOLTIP_PATTERN[granularity])
              }
              formatter={(value, name) => [
                formatElectricityValue(Number(value), unit),
                String(name),
              ]}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 13 }} />
            {(data?.buildings ?? []).map((building, index) => (
              <Bar
                key={building.building_id}
                dataKey={building.building_id}
                name={building.label}
                stackId="buildings"
                fill={
                  ELECTRICITY_BUILDING_COLORS[building.building_id] ??
                  buildingColor(building.building_id, index)
                }
                radius={index === (data?.buildings.length ?? 0) - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
                isAnimationActive={!isFetching}
              />
            ))}
            <Line
              type="monotone"
              dataKey="baseline"
              name="Base de centro cerrado"
              stroke="#64748b"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              isAnimationActive={!isFetching}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      {data && !isEmpty && (
        <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
          <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="font-heading text-lg font-semibold text-slate-900">
                Detalle por edificio
              </h3>
              <p className="text-xs text-muted-foreground">
                Total, media, mínimo y máximo por {ELECTRICITY_GRANULARITY_NOUN[data.granularity]}.
              </p>
            </div>
            <ExportCsvButton
              filename={`electricidad-edificios-${data.start}-${data.end}.csv`}
              headers={['Edificio', 'Total', 'Media', 'Mínimo', 'Máximo', '% centro']}
              rows={tableRows}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Edificio</th>
                  <th className="py-2 pr-4 text-right font-semibold">Total</th>
                  <th className="py-2 pr-4 text-right font-semibold">Media</th>
                  <th className="py-2 pr-4 text-right font-semibold">Mín.</th>
                  <th className="py-2 pr-4 text-right font-semibold">Máx.</th>
                  <th className="py-2 text-right font-semibold">% centro</th>
                </tr>
              </thead>
              <tbody>
                {data.buildings.map((building) => (
                  <tr key={building.building_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-800">{building.label}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatElectricityValue(building.total, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(building.average, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(building.minimum, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(building.maximum, unit)}
                    </td>
                    <td className="py-2 text-right tabular-nums text-slate-600">
                      {formatPercent(building.share * 100, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Fermín Caballero se calcula como Cuadro General − Módulo A − Módulo B. Los cuadros de
            planta y el CPD son subcontadores parciales de ese edificio.
          </p>
        </div>
      )}
    </div>
  );
}
