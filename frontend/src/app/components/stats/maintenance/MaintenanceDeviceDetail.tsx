import {
  Bar,
  CartesianGrid,
  ComposedChart,
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
  BATTERY_BG_CLASS,
  MATRIX_BG_CLASS,
  OUTAGE_SCOPE_BG_CLASS,
  formatDateRange,
  formatDurationHours,
} from '../../../lib/maintenance';
import {
  BATTERY_STATUS_LABEL,
  MATRIX_CATEGORY_LABEL,
  OUTAGE_SCOPE_LABEL,
} from '../../../types/maintenance';
import type {
  BatteryUnit,
  MaintenanceBatteryPointDto,
  MaintenanceDailyPointDto,
  MaintenanceDeviceDetailDto,
  MaintenanceOutageDto,
} from '../../../types/maintenance';
import { useMaintenanceDevice } from '../../../hooks/useMaintenance';

interface MaintenanceDeviceDetailProps {
  deviceId: string;
  days: number;
}

interface BatteryTooltipProps {
  active?: boolean;
  payload?: Array<{ payload?: { pct: number | null; value: number | null } }>;
  label?: string | number;
  unit: BatteryUnit | null;
}

function BatteryTooltip({ active, payload, label, unit }: BatteryTooltipProps) {
  const point = payload?.[0]?.payload;
  if (!active || !point || label === undefined) return null;
  return (
    <div style={TOOLTIP_STYLE} className="px-3 py-2">
      <p className="mb-1 font-semibold">
        {formatTimestamp(String(label), 'd MMM yyyy HH:mm')}
      </p>
      <p>Estimado: {point.pct === null ? '—' : `${formatNumber(point.pct, 0)} %`}</p>
      <p>
        Lectura:{' '}
        {point.value === null
          ? '—'
          : unit === 'millivolt'
            ? `${formatNumber(point.value, 0)} mV`
            : `${formatNumber(point.value, 0)} %`}
      </p>
    </div>
  );
}

function batteryChartData(points: MaintenanceBatteryPointDto[]) {
  return points.map((point) => ({
    timestamp: point.timestamp,
    pct: point.estimated_pct,
    value: point.value,
  }));
}

function dailyChartData(points: MaintenanceDailyPointDto[]) {
  return points.map((point) => ({
    date: point.date,
    updates: point.updates,
    expected: point.expected,
  }));
}

function OutageList({ outages }: { outages: MaintenanceOutageDto[] }) {
  if (outages.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        Sin cortes individuales ni globales que afecten a este dispositivo.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {outages.map((outage) => (
        <li
          key={`${outage.scope}-${outage.start}-${outage.end}`}
          className="flex flex-wrap items-center justify-between gap-2 rounded-sm border border-slate-200 px-3 py-2"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-sm border px-2 py-0.5 text-[11px] font-semibold ${OUTAGE_SCOPE_BG_CLASS[outage.scope]}`}
            >
              {OUTAGE_SCOPE_LABEL[outage.scope]}
            </span>
            <span className="text-sm font-semibold text-slate-800">
              {formatDurationHours(outage.duration_hours)}
            </span>
            {outage.ongoing && (
              <span className="rounded-sm border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
                En curso
              </span>
            )}
          </div>
          <span className="text-xs text-slate-500">
            {formatDateRange(outage.start, outage.end)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function DetailContent({ detail }: { detail: MaintenanceDeviceDetailDto }) {
  const { device } = detail;
  const battery = device.battery;
  const batteryData = batteryChartData(detail.battery_history);
  const dailyData = dailyChartData(detail.daily);
  const hasBatteryHistory = batteryData.some((point) => point.pct !== null);
  const hasDaily = dailyData.length > 0;

  return (
    <div className="space-y-4">
      <div
        className={`rounded-sm border px-3 py-2 text-sm font-semibold ${MATRIX_BG_CLASS[device.matrix_category]}`}
      >
        <span className="mr-2 rounded-sm bg-white/70 px-1.5 py-0.5 text-[11px] uppercase tracking-[0.08em]">
          {MATRIX_CATEGORY_LABEL[device.matrix_category]}
        </span>
        {device.decision}
      </div>

      <div className="flex flex-wrap gap-2">
        {battery && (
          <span
            className={`rounded-sm border px-2 py-0.5 text-[11px] font-semibold ${BATTERY_BG_CLASS[battery.status]}`}
          >
            Batería {BATTERY_STATUS_LABEL[battery.status].toLowerCase()}
          </span>
        )}
        {battery?.replacement_in_period && (
          <span className="rounded-sm border border-sky-200 bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-700">
            Cambio detectado
          </span>
        )}
        {battery?.stale && (
          <span className="rounded-sm border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
            Lectura antigua
          </span>
        )}
      </div>

      {device.reasons.length > 0 && (
        <ul className="list-disc space-y-1 pl-5 text-xs text-slate-600">
          {device.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {device.has_battery && (
          <ChartCard
            title="Historial de batería"
            subtitle={
              battery?.unit === 'millivolt'
                ? 'Porcentaje estimado a partir del voltaje'
                : 'Lecturas de batería y umbrales orientativos'
            }
            unit="%"
            isLoading={false}
            error={null}
            isEmpty={!hasBatteryHistory}
            emptyMessage="Sin historial de batería en los últimos 90 días."
            onRetry={() => undefined}
            height={230}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={batteryData}
                margin={{ top: 8, right: 12, bottom: 4, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => formatTimestamp(String(value), 'd MMM')}
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
                  width={36}
                />
                <ReferenceLine y={20} stroke="#ef4444" strokeDasharray="4 4" />
                <ReferenceLine y={40} stroke="#f59e0b" strokeDasharray="4 4" />
                <Tooltip
                  content={<BatteryTooltip unit={battery?.unit ?? null} />}
                />
                <Line
                  type="monotone"
                  dataKey="pct"
                  name="Batería estimada"
                  stroke="#0497d7"
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        <ChartCard
          title="Transmisión diaria"
          subtitle="Datos recibidos frente a los esperados"
          unit="datos"
          isLoading={false}
          error={null}
          isEmpty={!hasDaily}
          emptyMessage="Sin datos de transmisión para el periodo."
          onRetry={() => undefined}
          height={230}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={dailyData}
              margin={{ top: 8, right: 12, bottom: 4, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  formatTimestamp(`${String(value)}T12:00:00`, 'd MMM')
                }
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                minTickGap={20}
              />
              <YAxis
                tickFormatter={(value) => formatNumber(Number(value), 0)}
                tick={AXIS_TICK}
                tickLine={AXIS_LINE}
                axisLine={AXIS_LINE}
                width={36}
              />
              <Tooltip
                formatter={(value, name) => [
                  formatNumber(Number(value), 1),
                  name === 'updates' ? 'Recibidos' : 'Esperados',
                ]}
                labelFormatter={(value) =>
                  formatTimestamp(`${String(value)}T12:00:00`, 'EEEE d MMM yyyy')
                }
                contentStyle={TOOLTIP_STYLE}
              />
              <Legend wrapperStyle={{ color: '#334155', fontSize: 12 }} />
              <Bar
                dataKey="updates"
                name="Recibidos"
                fill="#0497d7"
                radius={[2, 2, 0, 0]}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="expected"
                name="Esperados"
                stroke="#cf6c2e"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div>
        <h4 className="mb-2 font-heading text-sm font-semibold text-slate-900">
          Cortes del dispositivo
        </h4>
        <OutageList outages={detail.outages} />
      </div>
    </div>
  );
}

export function MaintenanceDeviceDetail({
  deviceId,
  days,
}: MaintenanceDeviceDetailProps) {
  const { data, isLoading, error, retry } = useMaintenanceDevice(deviceId, days);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-sm border border-destructive/35 bg-white p-4">
        <p className="font-semibold text-destructive">
          No se pudo cargar el detalle del dispositivo.
        </p>
        <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
        <button
          type="button"
          onClick={retry}
          className="mt-3 rounded-sm bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return null;

  return <DetailContent detail={data} />;
}
