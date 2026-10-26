import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
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
  SECTOR_COLORS,
  TOOLTIP_STYLE,
  UNMETERED_COLOR,
} from '../../../lib/chartTheme';
import { ELECTRICITY_GRANULARITY_NOUN } from '../../../types/electricity';
import type { ElectricityDto } from '../../../types/electricity';

interface ElectricitySectorsChartProps {
  data: ElectricityDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function ElectricitySectorsChart({
  data,
  isLoading,
  isFetching,
  error,
  retry,
}: ElectricitySectorsChartProps) {
  const granularity = data?.granularity ?? 'day';
  const noun = ELECTRICITY_GRANULARITY_NOUN[granularity];
  const unit = data?.unit ?? 'kWh';
  const activeSectors = (data?.sectors ?? []).filter((sector) => sector.has_data);
  const unavailableSectors = (data?.sectors ?? []).filter((sector) => !sector.has_data);
  const fermin = data?.buildings.find((building) => building.building_id === 'FerminCaballero');

  const rows = (data?.series ?? []).map((point, index) => {
    const row: Record<string, string | number> = { timestamp: point.timestamp };
    let measured = 0;
    for (const sector of activeSectors) {
      const value = sector.series[index]?.value ?? 0;
      row[sector.sector_id] = value;
      measured += value;
    }
    const ferminValue = fermin?.series[index]?.value ?? 0;
    row.unmetered = Math.max(0, ferminValue - measured);
    return row;
  });

  const unmeteredValues = rows.map((row) => Number(row.unmetered));
  const unmeteredAverage = unmeteredValues.length
    ? unmeteredValues.reduce((total, value) => total + value, 0) / unmeteredValues.length
    : 0;
  const unmeteredMinimum = unmeteredValues.length ? Math.min(...unmeteredValues) : 0;
  const unmeteredMaximum = unmeteredValues.length ? Math.max(...unmeteredValues) : 0;
  const unmeteredShare = data?.fermin_total ? data.unmetered_total / data.fermin_total : 0;
  const isEmpty = !data || data.series.length === 0 || activeSectors.length === 0;

  const csvRows = [
    ...activeSectors.map((sector) => [
      sector.label,
      sector.floor,
      sector.total,
      sector.average,
      sector.minimum,
      sector.maximum,
      Number((sector.share_of_building * 100).toFixed(1)),
    ]),
    [
      'No desglosado',
      'Fermín Caballero',
      data?.unmetered_total ?? 0,
      Number(unmeteredAverage.toFixed(2)),
      Number(unmeteredMinimum.toFixed(2)),
      Number(unmeteredMaximum.toFixed(2)),
      Number((unmeteredShare * 100).toFixed(1)),
    ],
    ...unavailableSectors.map((sector) => [
      sector.label,
      sector.floor,
      'Sin datos',
      null,
      null,
      null,
      null,
    ]),
  ];

  return (
    <div className="space-y-4">
      <ChartCard
        title="Sectores de Fermín Caballero"
        subtitle={`${metricLabel(data?.metric ?? 'kwh')} por ${noun} · cuadros de planta y CPD; el resto se muestra como no desglosado`}
        unit={data?.unit}
        isLoading={isLoading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Sin datos de los cuadros de planta para el periodo seleccionado."
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
            <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
            {activeSectors.map((sector, index) => (
              <Bar
                key={sector.sector_id}
                dataKey={sector.sector_id}
                name={sector.label}
                stackId="sectors"
                fill={SECTOR_COLORS[index % SECTOR_COLORS.length]}
                isAnimationActive={!isFetching}
              />
            ))}
            <Bar
              dataKey="unmetered"
              name="No desglosado"
              stackId="sectors"
              fill={UNMETERED_COLOR}
              radius={[4, 4, 0, 0]}
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
                Detalle de sectores
              </h3>
              <p className="text-xs text-muted-foreground">
                Cobertura medida: {formatPercent(data.sector_coverage * 100, 1)} de Fermín
                Caballero.
              </p>
            </div>
            <ExportCsvButton
              filename={`electricidad-sectores-${data.start}-${data.end}.csv`}
              headers={[
                'Sector',
                'Planta',
                'Total',
                'Media',
                'Mínimo',
                'Máximo',
                '% Fermín',
              ]}
              rows={csvRows}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <th className="py-2 pr-4 font-semibold">Sector</th>
                  <th className="py-2 pr-4 font-semibold">Planta</th>
                  <th className="py-2 pr-4 text-right font-semibold">Total</th>
                  <th className="py-2 pr-4 text-right font-semibold">Media</th>
                  <th className="py-2 pr-4 text-right font-semibold">Mín.</th>
                  <th className="py-2 pr-4 text-right font-semibold">Máx.</th>
                  <th className="py-2 text-right font-semibold">% Fermín</th>
                </tr>
              </thead>
              <tbody>
                {activeSectors.map((sector) => (
                  <tr key={sector.sector_id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 font-medium text-slate-800">{sector.label}</td>
                    <td className="py-2 pr-4 text-slate-600">{sector.floor}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                      {formatElectricityValue(sector.total, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(sector.average, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(sector.minimum, unit)}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                      {formatElectricityValue(sector.maximum, unit)}
                    </td>
                    <td className="py-2 text-right tabular-nums text-slate-600">
                      {formatPercent(sector.share_of_building * 100, 1)}
                    </td>
                  </tr>
                ))}
                <tr className="border-b border-slate-100 bg-slate-50/70">
                  <td className="py-2 pr-4 font-medium text-slate-700">No desglosado</td>
                  <td className="py-2 pr-4 text-slate-600">Fermín Caballero</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-800">
                    {formatElectricityValue(data.unmetered_total, unit)}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                    {formatElectricityValue(unmeteredAverage, unit)}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                    {formatElectricityValue(unmeteredMinimum, unit)}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-700">
                    {formatElectricityValue(unmeteredMaximum, unit)}
                  </td>
                  <td className="py-2 text-right tabular-nums text-slate-600">
                    {formatPercent(unmeteredShare * 100, 1)}
                  </td>
                </tr>
                {unavailableSectors.map((sector) => (
                  <tr key={sector.sector_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-slate-500">{sector.label}</td>
                    <td className="py-2 pr-4 text-slate-500">{sector.floor}</td>
                    <td className="py-2 pr-4 text-xs text-slate-500" colSpan={5}>
                      {sector.note || 'Sin datos en el periodo disponible'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Los cuadros de planta y el CPD son subcontadores parciales. La barra gris «No
            desglosado» es la diferencia entre el total de Fermín y la suma de los cuadros
            medidos; no se reparte entre los sectores.
          </p>
        </div>
      )}
    </div>
  );
}
