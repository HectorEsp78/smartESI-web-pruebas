import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
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

interface ChartProps {
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

function TemperatureTooltip({
  active,
  payload,
  label,
  granularity,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number | null; color?: string }>;
  label?: string | number;
  granularity: EnvironmentGranularity;
}) {
  if (!active || !payload?.length || label === undefined) return null;
  return (
    <div style={TOOLTIP_STYLE} className="px-3 py-2">
      <p className="mb-1 font-semibold">{formatTimestamp(label, tooltipPattern(granularity))}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}:{' '}
          {entry.value === null || entry.value === undefined
            ? '—'
            : `${formatNumber(Number(entry.value), 1)} °C`}
        </p>
      ))}
    </div>
  );
}

export function EnvironmentRoomTemperatureChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: ChartProps) {
  const hasTemperature = series.some((point) => point.temperature_c !== null);
  const hasAmbient = series.some((point) => point.ambient_temperature_c !== null);

  return (
    <ChartCard
      title="Temperatura"
      subtitle="Estancia y ambiente de referencia"
      unit="°C"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasTemperature}
      emptyMessage="Sin datos de temperatura para el periodo seleccionado."
      onRetry={retry}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
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
            domain={['auto', 'auto']}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={40}
          />
          <ReferenceArea y1={18} y2={24} fill="#10b981" fillOpacity={0.06} />
          <ReferenceLine y={18} stroke="#10b981" strokeDasharray="4 4" />
          <ReferenceLine y={24} stroke="#10b981" strokeDasharray="4 4" />
          <Tooltip content={<TemperatureTooltip granularity={granularity} />} />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="temperature_c"
            name="Estancia"
            stroke="#0497d7"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          {hasAmbient && (
            <Line
              type="monotone"
              dataKey="ambient_temperature_c"
              name="Ambiente de referencia"
              stroke="#94a3b8"
              strokeWidth={1.5}
              strokeDasharray="5 4"
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function EnvironmentRoomHumidityChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: ChartProps) {
  const hasHumidity = series.some((point) => point.humidity_pct !== null);

  return (
    <ChartCard
      title="Humedad relativa"
      subtitle="Zona de confort orientativa: 30–60 %"
      unit="%"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasHumidity}
      emptyMessage="Sin datos de humedad para el periodo seleccionado."
      onRetry={retry}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
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
            domain={[0, 100]}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={40}
          />
          <ReferenceArea y1={30} y2={60} fill="#10b981" fillOpacity={0.06} />
          <ReferenceLine y={30} stroke="#10b981" strokeDasharray="4 4" />
          <ReferenceLine y={60} stroke="#10b981" strokeDasharray="4 4" />
          <Tooltip
            formatter={(value) => [`${formatNumber(Number(value), 1)} %`, 'Humedad']}
            labelFormatter={(value) => formatTimestamp(String(value), tooltipPattern(granularity))}
            contentStyle={TOOLTIP_STYLE}
          />
          <Line
            type="monotone"
            dataKey="humidity_pct"
            name="Humedad"
            stroke="#0891b2"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
