import {
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
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { formatNumber, formatTimestamp } from '../../../lib/format';
import type {
  EnvironmentGranularity,
  EnvironmentSeriesPointDto,
} from '../../../types/environment';

interface Props {
  series: EnvironmentSeriesPointDto[];
  granularity: EnvironmentGranularity;
  isLoading: boolean;
  error: Error | null;
  retry: () => void;
}

function tickPattern(granularity: EnvironmentGranularity): string {
  if (granularity === 'hour') return 'HH:mm';
  return 'd MMM';
}

function tooltipPattern(granularity: EnvironmentGranularity): string {
  if (granularity === 'hour') return 'EEEE d MMM, HH:mm';
  if (granularity === 'day') return 'EEEE d MMM yyyy';
  return "'Semana del' d MMM yyyy";
}

export function EnvironmentRoomCo2Chart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: Props) {
  const hasCo2 = series.some((point) => point.co2_ppm !== null);

  return (
    <ChartCard
      title="CO₂ y presencia"
      subtitle="Los picos de CO₂ deben coincidir con las horas ocupadas"
      unit="ppm"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasCo2}
      emptyMessage="Sin datos de CO₂ para el periodo seleccionado."
      onRetry={retry}
      height={300}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={series} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => formatTimestamp(String(value), tickPattern(granularity))}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            minTickGap={28}
          />
          <YAxis
            yAxisId="co2"
            domain={[300, 'auto']}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <YAxis
            yAxisId="presence"
            orientation="right"
            domain={[0, 100]}
            tickFormatter={(value) => `${formatNumber(Number(value), 0)}%`}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={42}
          />
          <ReferenceLine yAxisId="co2" y={800} stroke="#f59e0b" strokeDasharray="4 4" />
          <ReferenceLine yAxisId="co2" y={1000} stroke="#b30139" strokeDasharray="4 4" />
          <Tooltip
            formatter={(value, name) => {
              if (name === 'Ocupación') return [`${formatNumber(Number(value), 0)} %`, name];
              return [`${formatNumber(Number(value), 0)} ppm`, name];
            }}
            labelFormatter={(value) =>
              formatTimestamp(String(value), tooltipPattern(granularity))
            }
            contentStyle={TOOLTIP_STYLE}
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            yAxisId="co2"
            type="monotone"
            dataKey="co2_ppm"
            name="CO₂"
            stroke="#cf6c2e"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          <Line
            yAxisId="presence"
            type="monotone"
            dataKey="presence_pct"
            name="Ocupación"
            stroke="#2b8b57"
            strokeWidth={1.5}
            strokeDasharray="5 4"
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
