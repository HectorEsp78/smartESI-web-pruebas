import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
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
  WeatherGranularity,
  WeatherSeriesPointDto,
} from '../../../types/weather';

interface WeatherChartProps {
  series: WeatherSeriesPointDto[];
  granularity: WeatherGranularity;
  isLoading: boolean;
  error: Error | null;
  retry: () => void;
}

function tickPattern(granularity: WeatherGranularity): string {
  return granularity === 'hour' ? 'HH:mm' : 'd MMM';
}

function tooltipPattern(granularity: WeatherGranularity): string {
  return granularity === 'hour' ? 'EEEE d MMM, HH:mm' : 'EEEE d MMM yyyy';
}

interface TooltipEntry {
  name?: string;
  value?: number | string | null;
  color?: string;
  dataKey?: string;
}

function WeatherTooltip({
  active,
  payload,
  label,
  granularity,
  unit,
  digits,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
  granularity: WeatherGranularity;
  unit: string;
  digits: number;
}) {
  if (!active || !payload?.length || label === undefined) return null;
  return (
    <div style={TOOLTIP_STYLE} className="px-3 py-2">
      <p className="mb-1 font-semibold">
        {formatTimestamp(String(label), tooltipPattern(granularity))}
      </p>
      {payload.map((entry) => (
        <p key={entry.dataKey ?? entry.name} style={{ color: entry.color }}>
          {entry.name}:{' '}
          {entry.value === null || entry.value === undefined
            ? '—'
            : `${formatNumber(Number(entry.value), digits)} ${unit}`}
        </p>
      ))}
    </div>
  );
}

function commonAxisProps(granularity: WeatherGranularity) {
  return {
    dataKey: 'timestamp',
    tickFormatter: (value: string | number) =>
      formatTimestamp(String(value), tickPattern(granularity)),
    tick: AXIS_TICK,
    tickLine: AXIS_LINE,
    axisLine: AXIS_LINE,
    minTickGap: 28,
  };
}

export function WeatherTemperatureChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: WeatherChartProps) {
  const hasTemperature = series.some((point) => point.temperature_c !== null);
  const hasIndoor = series.some((point) => point.indoor_temperature_c !== null);
  const hasAemet = series.some((point) => point.aemet_temperature_c !== null);

  return (
    <ChartCard
      title="Temperatura"
      subtitle="Estación, interior de referencia y AEMET"
      unit="°C"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasTemperature}
      emptyMessage="Sin datos de temperatura para el periodo seleccionado."
      onRetry={retry}
      height={270}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...commonAxisProps(granularity)} />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={40}
          />
          <ReferenceLine y={30} stroke="#cf6c2e" strokeDasharray="4 4" />
          <ReferenceLine y={10} stroke="#0497d7" strokeDasharray="4 4" />
          <Tooltip
            content={
              <WeatherTooltip
                granularity={granularity}
                unit="°C"
                digits={1}
              />
            }
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="temperature_c"
            name="Estación"
            stroke="#0497d7"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          {hasIndoor && (
            <Line
              type="monotone"
              dataKey="indoor_temperature_c"
              name="Interior (sensor.ambiente)"
              stroke="#2b8b57"
              strokeWidth={1.5}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          )}
          {hasAemet && (
            <Line
              type="monotone"
              dataKey="aemet_temperature_c"
              name="AEMET (referencia)"
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

export function WeatherHumidityChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: WeatherChartProps) {
  const hasHumidity = series.some((point) => point.humidity_pct !== null);
  const hasIndoor = series.some((point) => point.indoor_humidity_pct !== null);
  const hasAemet = series.some((point) => point.aemet_humidity_pct !== null);

  return (
    <ChartCard
      title="Humedad relativa"
      subtitle="Estación, interior de referencia y AEMET"
      unit="%"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasHumidity}
      emptyMessage="Sin datos de humedad para el periodo seleccionado."
      onRetry={retry}
      height={270}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...commonAxisProps(granularity)} />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={40}
          />
          <ReferenceLine y={30} stroke="#10b981" strokeDasharray="4 4" />
          <ReferenceLine y={80} stroke="#cf6c2e" strokeDasharray="4 4" />
          <Tooltip
            content={
              <WeatherTooltip granularity={granularity} unit="%" digits={1} />
            }
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="humidity_pct"
            name="Estación"
            stroke="#0891b2"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          {hasIndoor && (
            <Line
              type="monotone"
              dataKey="indoor_humidity_pct"
              name="Interior (sensor.ambiente)"
              stroke="#2b8b57"
              strokeWidth={1.5}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          )}
          {hasAemet && (
            <Line
              type="monotone"
              dataKey="aemet_humidity_pct"
              name="AEMET (referencia)"
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

export function WeatherPressureChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: WeatherChartProps) {
  const hasPressure = series.some((point) => point.pressure_hpa !== null);

  return (
    <ChartCard
      title="Presión atmosférica"
      subtitle="Presión de la estación reducida al nivel del mar"
      unit="hPa"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasPressure}
      emptyMessage="Sin datos de presión para el periodo seleccionado."
      onRetry={retry}
      height={270}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...commonAxisProps(granularity)} />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <Tooltip
            content={
              <WeatherTooltip
                granularity={granularity}
                unit="hPa"
                digits={1}
              />
            }
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="pressure_hpa"
            name="Presión (nivel del mar)"
            stroke="#1f6f9a"
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

export function WeatherPmChart({
  series,
  granularity,
  isLoading,
  error,
  retry,
}: WeatherChartProps) {
  const hasPm = series.some((point) => point.pm25 !== null);

  return (
    <ChartCard
      title="Partículas en suspensión"
      subtitle="Índice relativo del sensor; no se compara con umbrales sanitarios"
      unit="índice"
      isLoading={isLoading}
      error={error}
      isEmpty={!hasPm}
      emptyMessage="Sin datos de partículas para el periodo seleccionado."
      onRetry={retry}
      height={270}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...commonAxisProps(granularity)} />
          <YAxis
            domain={[0, 'auto']}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <Tooltip
            content={
              <WeatherTooltip
                granularity={granularity}
                unit="índice"
                digits={0}
              />
            }
          />
          <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="pm1"
            name="PM1"
            stroke="#2b8b57"
            strokeWidth={1.5}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="pm25"
            name="PM2.5"
            stroke="#cf6c2e"
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="pm10"
            name="PM10"
            stroke="#b30139"
            strokeWidth={1.5}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
