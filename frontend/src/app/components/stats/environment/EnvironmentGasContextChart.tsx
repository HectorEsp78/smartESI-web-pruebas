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
import { StatCard } from '../../ui/StatCard';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { formatNumber, formatTimestamp } from '../../../lib/format';
import {
  formatGasCost,
  formatGasVolume,
  formatTemperature,
} from '../../../lib/environment';
import type {
  EnvironmentContextDto,
  EnvironmentGranularity,
  EnvironmentSeriesPointDto,
} from '../../../types/environment';

interface Props {
  series: EnvironmentSeriesPointDto[];
  context: EnvironmentContextDto;
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

export function EnvironmentGasContextChart({
  series,
  context,
  granularity,
  isLoading,
  error,
  retry,
}: Props) {
  const hasGas = context.has_gas && series.some((point) => point.gas_cost_eur !== null);
  const hasTemperature = series.some((point) => point.temperature_c !== null);
  const hasAmbient = series.some((point) => point.ambient_temperature_c !== null);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Gasto de gas"
          value={formatGasCost(context.gas_cost_eur)}
          hint="Periodo seleccionado · edificio"
        />
        <StatCard
          label="Consumo de gas"
          value={formatGasVolume(context.gas_m3)}
          hint="Periodo seleccionado · edificio"
        />
        <StatCard
          label="Coste medio diario"
          value={formatGasCost(context.gas_cost_per_day_eur)}
          hint="Gas del edificio, no solo de la estancia"
        />
        <StatCard
          label="Estancia − ambiente"
          value={
            context.avg_indoor_minus_ambient_c === null
              ? '—'
              : `${formatNumber(context.avg_indoor_minus_ambient_c, 1)} °C`
          }
          hint={`Ambiente actual ${formatTemperature(context.current_ambient_temperature_c)}`}
          tone={
            context.avg_indoor_minus_ambient_c !== null &&
            context.avg_indoor_minus_ambient_c > 3
              ? 'warning'
              : 'neutral'
          }
        />
      </div>

      <ChartCard
        title="Temperatura y calefacción"
        subtitle="Temperatura de la estancia, ambiente de referencia y coste de gas del edificio"
        unit="°C · €"
        isLoading={isLoading}
        error={error}
        isEmpty={!hasAmbient && !hasGas && !hasTemperature}
        emptyMessage="Sin datos de temperatura, ambiente o gas para el periodo seleccionado."
        onRetry={retry}
        height={300}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={series} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
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
              yAxisId="temperature"
              domain={['auto', 'auto']}
              tickFormatter={(value) => formatNumber(Number(value), 0)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={40}
            />
            <YAxis
              yAxisId="gas"
              orientation="right"
              tickFormatter={(value) => formatNumber(Number(value), 1)}
              tick={AXIS_TICK}
              tickLine={AXIS_LINE}
              axisLine={AXIS_LINE}
              width={48}
            />
            <Tooltip
              formatter={(value, name) => {
                if (name === 'Gas') return [formatGasCost(Number(value)), name];
                return [`${formatNumber(Number(value), 1)} °C`, name];
              }}
              labelFormatter={(value) =>
                formatTimestamp(String(value), tooltipPattern(granularity))
              }
              contentStyle={TOOLTIP_STYLE}
            />
            <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
            <Bar
              yAxisId="gas"
              dataKey="gas_cost_eur"
              name="Gas"
              fill="#f59e0b"
              fillOpacity={0.35}
              isAnimationActive={false}
            />
            <Line
              yAxisId="temperature"
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
                yAxisId="temperature"
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
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      <p className="text-[11px] text-slate-500">
        El gas es una medida del edificio y puede incluir otros usos además de la calefacción.
        El sensor de ambiente no tiene una sala confirmada; se usa solo como referencia.
      </p>
    </div>
  );
}
