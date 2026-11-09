import { useEffect, useRef, useState } from 'react';
import { BatteryHistoryChart } from './BatteryHistoryChart';
import { ChartCard } from '../../ui/ChartCard';
import { DateInput } from '../../ui/DateInput';
import { useBatteryHistory } from '../../../hooks/useBattery';
import { todayIso } from '../../../lib/electricity';
import type { DatePeriod } from '../../../lib/electricity';
import {
  defaultHistoryPeriod,
  formatBatteryValue,
  historyPeriodError,
  historyShortcuts,
} from '../../../lib/battery';
import type { BatterySensorDto } from '../../../types/battery';

interface BatteryHistoryDialogProps {
  groupId: string;
  sensor: BatterySensorDto;
  onClose: () => void;
}

export function BatteryHistoryDialog({ groupId, sensor, onClose }: BatteryHistoryDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [period, setPeriod] = useState<DatePeriod>(() => defaultHistoryPeriod(sensor.reading_at));
  const periodError = historyPeriodError(period);
  const { data, isLoading, error, retry } = useBatteryHistory(
    groupId,
    sensor.id,
    periodError ? null : period,
  );
  const today = todayIso();
  const hasReadings = data?.points.some((point) => point.value !== null) ?? false;
  const subtitle = data
    ? `${data.granularity === 'hour' ? 'Media por hora' : 'Media por día'} · Mín. ${formatBatteryValue(data.min_value, data.unit)} · Máx. ${formatBatteryValue(data.max_value, data.unit)}`
    : 'Cargando…';

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  return (
    // The click only adds closing from the backdrop: Escape and the button cover the keyboard.
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <dialog
      ref={dialogRef}
      aria-labelledby="battery-history-title"
      onClose={onClose}
      onClick={(event) => {
        // A click on the dialog element itself is a click on the backdrop.
        if (event.target === dialogRef.current) onClose();
      }}
      className="m-auto w-[min(60rem,calc(100vw-2rem))] rounded-md bg-slate-50 p-0 backdrop:bg-slate-900/50"
    >
      <div className="space-y-4 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3
              id="battery-history-title"
              className="font-heading text-xl font-semibold text-slate-900"
            >
              {sensor.label}
            </h3>
            <p className="break-all text-xs text-muted-foreground">{sensor.entity_id}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 cursor-pointer rounded-sm border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:border-primary hover:text-primary"
          >
            Cerrar
          </button>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-end gap-4">
            <DateInput
              label="Desde"
              value={period.start}
              max={today}
              onChange={(start) => setPeriod({ ...period, start })}
            />
            <DateInput
              label="Hasta"
              value={period.end}
              max={today}
              onChange={(end) => setPeriod({ ...period, end })}
            />
            <div
              className="flex flex-wrap items-center gap-1.5"
              role="group"
              aria-label="Periodos rápidos"
            >
              {historyShortcuts(today).map((shortcut) => {
                const isActive =
                  shortcut.period.start === period.start && shortcut.period.end === period.end;
                return (
                  <button
                    key={shortcut.label}
                    type="button"
                    onClick={() => setPeriod(shortcut.period)}
                    aria-pressed={isActive}
                    className={`cursor-pointer rounded-sm border px-3 py-1.5 text-xs transition-colors ${
                      isActive
                        ? 'border-primary bg-primary font-semibold text-primary-foreground'
                        : 'border-slate-300 bg-white text-slate-700 hover:border-primary hover:text-primary'
                    }`}
                  >
                    {shortcut.label}
                  </button>
                );
              })}
            </div>
          </div>
          {periodError && (
            <p className="mt-3 rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              {periodError}
            </p>
          )}
        </div>

        {!periodError && (
          <ChartCard
            title="Histórico de batería"
            subtitle={subtitle}
            unit={sensor.unit === 'millivolt' ? 'mV' : '%'}
            isLoading={isLoading}
            error={error}
            isEmpty={!hasReadings}
            emptyMessage="Sin lecturas válidas en este periodo."
            onRetry={retry}
            height={340}
          >
            {data && <BatteryHistoryChart history={data} />}
          </ChartCard>
        )}

        <p className="text-xs text-slate-500">
          Los huecos de la línea indican más de 7 días sin lecturas válidas.
        </p>
      </div>
    </dialog>
  );
}
