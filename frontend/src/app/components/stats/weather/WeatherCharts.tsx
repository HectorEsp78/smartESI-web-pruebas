import {
  Bar,
  BarChart,
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
import {
  AEMET_COLOR,
  STATION_COLOR,
  weatherTickPattern,
  weatherTooltipPattern,
} from '../../../lib/weather';
import type {
  HourlyBiasDto,
  WeatherGranularity,
  WeatherSeriesPointDto,
} from '../../../types/weather';

interface SeriesChartProps {
  series: WeatherSeriesPointDto[];
  granularity: WeatherGranularity;
}

type NumericKey = {
  [K in keyof WeatherSeriesPointDto]: WeatherSeriesPointDto[K] extends number | null ? K : never;
}[keyof WeatherSeriesPointDto];

const LEGEND_STYLE = { color: '#334155', fontSize: 12 };
const CHART_MARGIN = { top: 8, right: 16, bottom: 4, left: 0 };

function noRetry() {
  return undefined;
}

function hasValues(series: WeatherSeriesPointDto[], key: NumericKey): boolean {
  return series.some((point) => point[key] !== null);
}

function timeAxisProps(granularity: WeatherGranularity) {
  return {
    dataKey: 'timestamp',
    tickFormatter: (value: string | number) =>
      formatTimestamp(String(value), weatherTickPattern(granularity)),
    tick: AXIS_TICK,
    tickLine: AXIS_LINE,
    axisLine: AXIS_LINE,
    minTickGap: 36,
  };
}

function SeriesTooltip({
  active,
  payload,
  label,
  granularity,
  unit,
  digits,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number | string | null; color?: string; dataKey?: string }>;
  label?: string | number;
  granularity: WeatherGranularity;
  unit: string;
  digits: number;
}) {
  if (!active || !payload?.length || label === undefined) return null;
  const suffix = unit ? ` ${unit}` : '';
  return (
    <div style={TOOLTIP_STYLE} className="px-3 py-2">
      <p className="mb-1 font-semibold">
        {formatTimestamp(String(label), weatherTooltipPattern(granularity))}
      </p>
      {payload.map((entry) => (
        <p key={entry.dataKey ?? entry.name} style={{ color: entry.color }}>
          {entry.name}:{' '}
          {entry.value === null || entry.value === undefined
            ? 'sin dato'
            : `${formatNumber(Number(entry.value), digits)}${suffix}`}
        </p>
      ))}
    </div>
  );
}

/** A station line and an AEMET line on the same axis. A gap stays a gap. */
function ComparisonChart({
  series,
  granularity,
  title,
  subtitle,
  unit,
  stationKey,
  aemetKey,
  domain,
  digits,
}: SeriesChartProps & {
  title: string;
  subtitle: string;
  unit: string;
  stationKey: NumericKey;
  aemetKey: NumericKey;
  domain: [number | string, number | string];
  digits: number;
}) {
  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      unit={unit}
      isLoading={false}
      error={null}
      isEmpty={!hasValues(series, stationKey) && !hasValues(series, aemetKey)}
      onRetry={noRetry}
      height={300}
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <LineChart data={series} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...timeAxisProps(granularity)} />
          <YAxis
            domain={domain}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <Tooltip
            content={<SeriesTooltip granularity={granularity} unit={unit} digits={digits} />}
          />
          <Legend wrapperStyle={LEGEND_STYLE} />
          <Line
            type="monotone"
            dataKey={stationKey}
            name="Estación del centro"
            stroke={STATION_COLOR}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey={aemetKey}
            name="AEMET Ciudad Real"
            stroke={AEMET_COLOR}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function WeatherTemperatureChart(props: SeriesChartProps) {
  return (
    <ComparisonChart
      {...props}
      title="Temperatura"
      subtitle="Estación del centro frente a AEMET"
      unit="°C"
      stationKey="station_temperature_c"
      aemetKey="aemet_temperature_c"
      domain={['auto', 'auto']}
      digits={1}
    />
  );
}

export function WeatherHumidityChart(props: SeriesChartProps) {
  return (
    <ComparisonChart
      {...props}
      title="Humedad relativa"
      subtitle="Estación del centro frente a AEMET"
      unit="%"
      stationKey="station_humidity_pct"
      aemetKey="aemet_humidity_pct"
      domain={[0, 100]}
      digits={1}
    />
  );
}

export function WeatherPressureChart(props: SeriesChartProps) {
  return (
    <ComparisonChart
      {...props}
      title="Presión"
      subtitle="Ambas a la altitud del observatorio de AEMET (626 m)"
      unit="hPa"
      stationKey="station_pressure_hpa"
      aemetKey="aemet_pressure_hpa"
      domain={['auto', 'auto']}
      digits={1}
    />
  );
}

export function WeatherHourlyBiasChart({ hourlyBias }: { hourlyBias: HourlyBiasDto[] }) {
  const data = hourlyBias.map((item) => ({
    hour: `${String(item.hour).padStart(2, '0')}:00`,
    bias: item.temperature_bias_c,
  }));

  return (
    <ChartCard
      title="Diferencia de temperatura por hora del día"
      subtitle="Estación − AEMET, en hora local: un pico de día apunta al efecto del sol"
      unit="°C"
      isLoading={false}
      error={null}
      isEmpty={!data.some((item) => item.bias !== null)}
      emptyMessage="Sin horas comparables con AEMET en este periodo."
      onRetry={noRetry}
      height={300}
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <BarChart data={data} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis
            dataKey="hour"
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            interval={2}
          />
          <YAxis
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <ReferenceLine y={0} stroke="#64748b" />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value) => [`${formatNumber(Number(value), 1)} °C`, 'Diferencia']}
            cursor={{ fill: 'rgba(4, 151, 215, 0.08)' }}
          />
          <Bar dataKey="bias" name="Diferencia" fill={STATION_COLOR} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function WeatherRainChart({ series, granularity }: SeriesChartProps) {
  return (
    <ChartCard
      title="Lluvia en Ciudad Real"
      subtitle={`Datos de AEMET, por ${granularity === 'hour' ? 'hora' : 'día'}; la estación no mide lluvia`}
      unit="mm"
      isLoading={false}
      error={null}
      isEmpty={!hasValues(series, 'aemet_precipitation_mm')}
      emptyMessage="Sin datos de lluvia de AEMET en este periodo."
      onRetry={noRetry}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <BarChart data={series} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis {...timeAxisProps(granularity)} />
          <YAxis
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <Tooltip
            content={<SeriesTooltip granularity={granularity} unit="mm" digits={1} />}
            cursor={{ fill: 'rgba(179, 1, 57, 0.08)' }}
          />
          <Bar
            dataKey="aemet_precipitation_mm"
            name="Lluvia"
            fill={AEMET_COLOR}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function WeatherPmChart({ series, granularity }: SeriesChartProps) {
  const lines: Array<{ key: NumericKey; name: string; color: string }> = [
    { key: 'pm1', name: 'PM1', color: '#2b8b57' },
    { key: 'pm25', name: 'PM2.5', color: STATION_COLOR },
    { key: 'pm10', name: 'PM10', color: '#cf6c2e' },
  ];

  return (
    <ChartCard
      title="Partículas"
      subtitle="Índice relativo de la estación: no publica unidad ni se compara con umbrales sanitarios"
      unit="índice"
      isLoading={false}
      error={null}
      isEmpty={!lines.some((line) => hasValues(series, line.key))}
      emptyMessage="Sin datos de partículas en este periodo."
      onRetry={noRetry}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <LineChart data={series} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...timeAxisProps(granularity)} />
          <YAxis
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={56}
          />
          <Tooltip content={<SeriesTooltip granularity={granularity} unit="" digits={0} />} />
          <Legend wrapperStyle={LEGEND_STYLE} />
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.name}
              stroke={line.color}
              strokeWidth={1.5}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function WeatherBatteryChart({ series, granularity }: SeriesChartProps) {
  return (
    <ChartCard
      title="Batería de la estación"
      subtitle="Evolución en el periodo"
      unit="%"
      isLoading={false}
      error={null}
      isEmpty={!hasValues(series, 'battery_pct')}
      emptyMessage="Sin datos de batería en este periodo."
      onRetry={noRetry}
      height={260}
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <LineChart data={series} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis {...timeAxisProps(granularity)} />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(value) => formatNumber(Number(value), 0)}
            tick={AXIS_TICK}
            tickLine={AXIS_LINE}
            axisLine={AXIS_LINE}
            width={48}
          />
          <Tooltip content={<SeriesTooltip granularity={granularity} unit="%" digits={0} />} />
          <Line
            type="monotone"
            dataKey="battery_pct"
            name="Batería"
            stroke="#2b8b57"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
