import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AXIS_LINE, AXIS_TICK, TOOLTIP_STYLE } from '../../../lib/chartTheme';
import { formatNumber, formatTimestamp } from '../../../lib/format';
import { formatBatteryValue, historyYDomain } from '../../../lib/battery';
import type { BatteryHistoryDto, BatteryUnit } from '../../../types/battery';

const LINE_COLOR = 'var(--primary)';
const LOW_COLOR = '#b45309';
const CRITICAL_COLOR = '#b91c1c';
/** With few readings the line alone can hide them. */
const MAX_POINTS_WITH_DOTS = 40;

interface ChartPoint {
  time: number;
  value: number | null;
  estimated_pct: number | null;
}

function HistoryTooltip({
  active,
  payload,
  pattern,
  unit,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ChartPoint }>;
  pattern: string;
  unit: BatteryUnit;
}) {
  const point = payload?.[0]?.payload;
  if (!active || !point || point.value === null) return null;

  return (
    <div style={TOOLTIP_STYLE} className="rounded-sm border px-3 py-2 text-xs">
      <p className="font-semibold">{formatTimestamp(point.time, pattern)}</p>
      <p>
        {formatBatteryValue(point.value, unit, unit === 'millivolt' ? 0 : 1)}
        {point.estimated_pct !== null && ` (≈ ${point.estimated_pct} % estimado)`}
      </p>
    </div>
  );
}

export function BatteryHistoryChart({ history }: { history: BatteryHistoryDto }) {
  const points: ChartPoint[] = history.points.map((point) => ({
    time: new Date(point.timestamp).getTime(),
    value: point.value,
    estimated_pct: point.estimated_pct,
  }));
  const isHourly = history.granularity === 'hour';
  const domain = historyYDomain(
    history.unit,
    history.min_value,
    history.max_value,
    history.critical_threshold,
  );

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
      <LineChart data={points} margin={{ top: 16, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis
          dataKey="time"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          tickFormatter={(value: number) =>
            formatTimestamp(value, isHourly ? "d MMM HH'h'" : 'd MMM yy')
          }
          tick={AXIS_TICK}
          tickLine={AXIS_LINE}
          axisLine={AXIS_LINE}
          minTickGap={48}
        />
        <YAxis
          domain={domain}
          tickFormatter={(value) => formatNumber(Number(value), 0)}
          tick={AXIS_TICK}
          tickLine={AXIS_LINE}
          axisLine={AXIS_LINE}
          width={56}
        />
        <Tooltip
          content={
            <HistoryTooltip
              pattern={isHourly ? 'EEEE d MMM yyyy, HH:mm' : 'EEEE d MMM yyyy'}
              unit={history.unit}
            />
          }
        />
        <ReferenceLine
          y={history.low_threshold}
          stroke={LOW_COLOR}
          strokeDasharray="4 4"
          label={{ value: 'Baja', position: 'insideTopRight', fill: LOW_COLOR, fontSize: 11 }}
        />
        <ReferenceLine
          y={history.critical_threshold}
          stroke={CRITICAL_COLOR}
          strokeDasharray="4 4"
          label={{ value: 'Crítica', position: 'insideTopRight', fill: CRITICAL_COLOR, fontSize: 11 }}
        />
        <Line
          type="linear"
          dataKey="value"
          name={history.label}
          stroke={LINE_COLOR}
          strokeWidth={2}
          dot={points.length <= MAX_POINTS_WITH_DOTS ? { r: 3 } : false}
          connectNulls={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
