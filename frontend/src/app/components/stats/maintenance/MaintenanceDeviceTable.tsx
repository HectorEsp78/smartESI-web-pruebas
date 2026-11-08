import { useMemo, useState } from 'react';
import { MaintenanceDeviceDetail } from './MaintenanceDeviceDetail';
import {
  BATTERY_BG_CLASS,
  DATA_STATUS_BG_CLASS,
  PRIORITY_BG_CLASS,
  filterMaintenanceDevices,
  formatAvailability,
  formatBatteryAge,
  formatBatteryPercent,
  formatBatteryValue,
  formatFrequency,
  formatDurationHours,
  maintenanceFilterCount,
} from '../../../lib/maintenance';
import type { MaintenanceFilter } from '../../../lib/maintenance';
import {
  BATTERY_STATUS_LABEL,
  DATA_STATUS_LABEL,
  HEARTBEAT_STATUS_LABEL,
  PRIORITY_LABEL,
} from '../../../types/maintenance';
import type { MaintenanceDeviceSummaryDto } from '../../../types/maintenance';

interface MaintenanceDeviceTableProps {
  devices: MaintenanceDeviceSummaryDto[];
  days: number;
}

const FILTERS: Array<{ id: MaintenanceFilter; label: string }> = [
  { id: 'all', label: 'Todos' },
  { id: 'priority', label: 'Prioritarios' },
  { id: 'low_battery', label: 'Batería baja' },
  { id: 'no_data', label: 'Sin datos' },
];

function BatteryCell({ device }: { device: MaintenanceDeviceSummaryDto }) {
  const battery = device.battery;
  if (!device.has_battery) {
    return <span className="text-xs text-slate-500">Alimentado por red</span>;
  }
  if (!battery || battery.status === 'unknown') {
    return <span className="text-xs text-slate-500">Sin lectura</span>;
  }
  return (
    <div className="space-y-0.5">
      <div className="flex flex-wrap items-center gap-1.5">
        <span
          className={`rounded-sm border px-1.5 py-0.5 text-[11px] font-semibold ${BATTERY_BG_CLASS[battery.status]}`}
        >
          {BATTERY_STATUS_LABEL[battery.status]}
        </span>
        <span className="text-xs font-semibold text-slate-800">
          {formatBatteryValue(battery)}
        </span>
        {battery.unit === 'millivolt' && (
          <span className="text-[11px] text-slate-500">
            ~{formatBatteryPercent(battery)}
          </span>
        )}
      </div>
      <p className="text-[11px] text-slate-500">{formatBatteryAge(battery)}</p>
    </div>
  );
}

function TransmissionCell({ device }: { device: MaintenanceDeviceSummaryDto }) {
  const { heartbeat } = device;
  return (
    <div className="space-y-0.5">
      <div className="flex flex-wrap items-center gap-1.5">
        <span
          className={`rounded-sm border px-1.5 py-0.5 text-[11px] font-semibold ${DATA_STATUS_BG_CLASS[device.data_status]}`}
        >
          {DATA_STATUS_LABEL[device.data_status]}
        </span>
        <span className="text-[11px] text-slate-500">
          {HEARTBEAT_STATUS_LABEL[heartbeat.status]}
        </span>
      </div>
      <p className="text-[11px] text-slate-500">
        {device.mode === 'event'
          ? 'Por eventos'
          : heartbeat.silence_hours !== null && !device.data_ok
            ? `Sin datos ${formatDurationHours(heartbeat.silence_hours)}`
            : formatFrequency(heartbeat.updates_per_day)}
      </p>
    </div>
  );
}

function DeviceRow({
  device,
  days,
  expanded,
  onToggle,
}: {
  device: MaintenanceDeviceSummaryDto;
  days: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className="border-t border-slate-100 align-top hover:bg-slate-50/70">
        <td className="px-3 py-2.5">
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={expanded}
            className="flex w-full items-start gap-2 text-left"
          >
            <span
              aria-hidden="true"
              className={`mt-0.5 inline-block text-[10px] text-slate-400 transition-transform ${
                expanded ? 'rotate-90' : ''
              }`}
            >
              ▶
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-slate-800">
                {device.label}
              </span>
              <span className="block truncate text-[11px] text-slate-500">
                {device.type}
                {device.location ? ` · ${device.location}` : ''}
              </span>
            </span>
          </button>
        </td>
        <td className="px-3 py-2.5">
          <span
            className={`inline-block rounded-sm border px-1.5 py-0.5 text-[11px] font-semibold ${PRIORITY_BG_CLASS[device.priority_label]}`}
          >
            {PRIORITY_LABEL[device.priority_label]}
          </span>
          <p className="mt-0.5 text-[11px] text-slate-500">{device.priority}/100</p>
        </td>
        <td className="px-3 py-2.5">
          <BatteryCell device={device} />
        </td>
        <td className="px-3 py-2.5">
          <TransmissionCell device={device} />
        </td>
        <td className="hidden px-3 py-2.5 text-xs font-semibold text-slate-700 md:table-cell">
          {formatAvailability(device.availability.availability_pct)}
          <p className="text-[11px] font-normal text-slate-500">
            {device.availability.outages_individual} cortes propios
          </p>
        </td>
      </tr>
      {expanded && (
        <tr className="border-t border-slate-100 bg-slate-50/60">
          <td colSpan={5} className="px-3 py-4">
            <MaintenanceDeviceDetail deviceId={device.id} days={days} />
          </td>
        </tr>
      )}
    </>
  );
}

export function MaintenanceDeviceTable({
  devices,
  days,
}: MaintenanceDeviceTableProps) {
  const [filter, setFilter] = useState<MaintenanceFilter>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(
    () => filterMaintenanceDevices(devices, filter),
    [devices, filter],
  );

  return (
    <section className="rounded-md border border-slate-200 bg-white">
      <div className="flex flex-wrap items-end justify-between gap-3 px-4 pt-4">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Dispositivos
          </h3>
          <p className="text-xs text-muted-foreground">
            Ordenados por prioridad. Pulsa una fila para ver batería, transmisión y cortes.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {FILTERS.map((option) => {
            const active = filter === option.id;
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => setFilter(option.id)}
                aria-pressed={active}
                className={`rounded-sm border px-2.5 py-1 text-xs font-semibold transition-colors ${
                  active
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-primary/40 hover:text-primary'
                }`}
              >
                {option.label}
                <span
                  className={`ml-1.5 rounded-sm px-1 text-[10px] ${
                    active ? 'bg-white/20' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {maintenanceFilterCount(devices, option.id)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="m-4 rounded-sm border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm text-slate-500">
          No hay dispositivos que cumplan este filtro.
        </p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-50 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                <th className="px-3 py-2">Dispositivo</th>
                <th className="px-3 py-2">Prioridad</th>
                <th className="px-3 py-2">Batería</th>
                <th className="px-3 py-2">Transmisión</th>
                <th className="hidden px-3 py-2 md:table-cell">Disponibilidad</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((device) => (
                <DeviceRow
                  key={device.id}
                  device={device}
                  days={days}
                  expanded={expandedId === device.id}
                  onToggle={() =>
                    setExpandedId((current) =>
                      current === device.id ? null : device.id,
                    )
                  }
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="border-t border-slate-100 px-4 py-2.5 text-[11px] text-slate-500">
        Mostrando {filtered.length} de {devices.length} dispositivos.
      </p>
    </section>
  );
}
