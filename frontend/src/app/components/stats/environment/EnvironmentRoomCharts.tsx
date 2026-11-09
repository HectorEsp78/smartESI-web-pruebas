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

function axisProps(granularity: EnvironmentGranularity) {
  return {
    dataKey: 'timestamp',
    tickFormatter: (value: string | number) =>
      formatTimestamp(String(value), tickPattern(granularity)),
    tick: AXIS_TICK,
    tickLine: AXIS_LINE,
    axisLine: AXIS_LINE,
    minTickGap: 28,
  } as const;
}

interface PresencePoint extends EnvironmentSeriesPointDto {
  presence_yes: number | null;
}

export function EnvironmentRoomTemperatureChart({ series, granularity }: ChartProps) {
  const hasData = series.some((point) => point.temperature_c !== null);

  return (
    <ChartCard
      title="Temperatura"
      subtitle="Zona de confort orientativa: 18–24 °C"
      unit="°C"
      isLoading={false}
      error={null}
      isEmpty={!hasData}
      emptyMessage="Sin datos de temperatura para el periodo seleccionado."
      onRetry={() => undefined}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...axisProps(granularity)} />
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
          <Tooltip
            formatter={(value) => [`${formatNumber(Number(value), 1)} °C`, 'Temperatura']}
            labelFormatter={(value) => formatTimestamp(String(value), tooltipPattern(granularity))}
            contentStyle={TOOLTIP_STYLE}
          />
          <Line
            type="monotone"
            dataKey="temperature_c"
            name="Temperatura"
            stroke="#f97316"
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

export function EnvironmentRoomHumidityChart({ series, granularity }: ChartProps) {
  const hasData = series.some((point) => point.humidity_pct !== null);

  return (
    <ChartCard
      title="Humedad relativa"
      subtitle="Zona de confort orientativa: 30–60 %"
      unit="%"
      isLoading={false}
      error={null}
      isEmpty={!hasData}
      emptyMessage="Sin datos de humedad para el periodo seleccionado."
      onRetry={() => undefined}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...axisProps(granularity)} />
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

export function EnvironmentRoomPresenceChart({ series, granularity }: ChartProps) {
  const data: PresencePoint[] = series.map((point) => ({
    ...point,
    presence_yes:
      point.presence_pct === null ? null : point.presence_pct > 0 ? 1 : 0,
  }));
  const hasData = data.some((point) => point.presence_yes !== null);

  return (
    <ChartCard
      title="Presencia"
      subtitle="Detección de movimiento en cada intervalo"
      isLoading={false}
      error={null}
      isEmpty={!hasData}
      emptyMessage="Sin datos de presencia para el periodo seleccionado."
      onRetry={() => undefined}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...axisProps(granularity)} />
          <YAxis
            domain={[0, 1]}
            ticks={[0, 1]}
            tickFormatter={(value) => (Number(value) === 1 ? 'Sí' : 'No')}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={40}
          />
          <Tooltip
            formatter={(value) => [Number(value) === 1 ? 'Sí' : 'No', 'Presencia']}
            labelFormatter={(value) => formatTimestamp(String(value), tooltipPattern(granularity))}
            contentStyle={TOOLTIP_STYLE}
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="stepAfter"
            dataKey="presence_yes"
            name="Presencia"
            stroke="#2b8b57"
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
