import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import { ChartCard } from '../../ui/ChartCard';
import { StatCard } from '../../ui/StatCard';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { formatNumber, formatPercent } from '../../../lib/format';
import {
  formatCo2,
  formatCorrelation,
} from '../../../lib/environment';
import type {
  EnvironmentCo2OccupancyDto,
  EnvironmentSeriesPointDto,
} from '../../../types/environment';

interface Props {
  points: EnvironmentSeriesPointDto[];
  stats: EnvironmentCo2OccupancyDto | null;
  isLoading: boolean;
  error: Error | null;
  retry: () => void;
}

export function EnvironmentCo2OccupancyCard({ points, stats, isLoading, error, retry }: Props) {
  const scatter = points.filter(
    (point) => point.co2_ppm !== null && point.presence_pct !== null,
  );
  const liftTone =
    stats?.lift_pct !== null && stats?.lift_pct !== undefined && stats.lift_pct > 20
      ? 'warning'
      : stats?.lift_pct !== null && stats?.lift_pct !== undefined
        ? 'success'
        : 'neutral';

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="CO₂ con presencia"
          value={formatCo2(stats?.occupied_co2_ppm ?? null)}
          hint={
            stats?.occupied_hours == null
              ? 'Sin datos'
              : `${formatNumber(stats.occupied_hours, 1)} h ocupadas`
          }
        />
        <StatCard
          label="CO₂ sin presencia"
          value={formatCo2(stats?.empty_co2_ppm ?? null)}
          hint={
            stats?.empty_hours == null
              ? 'Sin datos'
              : `${formatNumber(stats.empty_hours, 1)} h vacías`
          }
        />
        <StatCard
          label="Incremento"
          value={stats?.lift_pct == null ? '—' : formatPercent(stats.lift_pct, 0)}
          hint="CO₂ con presencia frente a vacío"
          tone={liftTone}
        />
        <StatCard
          label="Correlación"
          value={formatCorrelation(stats?.correlation ?? null)}
          hint="Pearson entre ocupación y CO₂"
          tone={
            stats?.correlation !== null && stats?.correlation !== undefined && stats.correlation >= 0.3
              ? 'success'
              : 'neutral'
          }
        />
      </div>

      <ChartCard
        title="CO₂ frente a ocupación"
        subtitle="Cada punto es un intervalo del periodo. Arriba y a la derecha: más ocupación y más CO₂."
        isLoading={isLoading}
        error={error}
        isEmpty={scatter.length === 0}
        emptyMessage="Sin datos conjuntos de CO₂ y presencia."
        onRetry={retry}
        height={300}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 20, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              type="number"
              dataKey="presence_pct"
              name="Ocupación"
              unit="%"
              domain={[0, 100]}
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
            />
            <YAxis
              type="number"
              dataKey="co2_ppm"
              name="CO₂"
              domain={[300, 'auto']}
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={48}
            />
            <ZAxis range={[40, 40]} />
            <Tooltip
              formatter={(value, name) => {
                if (name === 'Ocupación') return [formatPercent(Number(value), 0), name];
                return [formatCo2(Number(value)), name];
              }}
              contentStyle={TOOLTIP_STYLE}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Scatter
              name="Intervalos"
              data={scatter}
              fill="#0497d7"
              fillOpacity={0.55}
              isAnimationActive={false}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
