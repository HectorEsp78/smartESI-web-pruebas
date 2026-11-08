import type { CSSProperties } from 'react';
import {
  availabilityColor,
  formatAvailability,
  maintenanceHeatmap,
} from '../../../lib/maintenance';
import { formatNumber } from '../../../lib/format';
import type {
  MaintenanceDeviceSummaryDto,
  MaintenanceHeatmapCellDto,
} from '../../../types/maintenance';

interface MaintenanceHeatmapProps {
  devices: MaintenanceDeviceSummaryDto[];
  cells: MaintenanceHeatmapCellDto[];
}

export function MaintenanceHeatmap({ devices, cells }: MaintenanceHeatmapProps) {
  const { dates, rows } = maintenanceHeatmap(devices, cells);

  if (rows.length === 0 || dates.length === 0) {
    return (
      <section className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Transmisión diaria
        </h3>
        <p className="mt-3 rounded-sm border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm text-slate-500">
          Sin datos suficientes para construir el mapa de transmisión.
        </p>
      </section>
    );
  }

  const labelEvery = Math.max(1, Math.ceil(dates.length / 12));
  const cellWidth = 14;

  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Transmisión diaria
          </h3>
          <p className="text-xs text-muted-foreground">
            Datos recibidos frente a los esperados por día. Un corte global baja todas las
            filas a la vez.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-500">
          <span>0 %</span>
          <span
            className="h-2.5 w-6 rounded-[2px]"
            style={{ backgroundColor: availabilityColor(0) }}
          />
          <span
            className="h-2.5 w-6 rounded-[2px]"
            style={{ backgroundColor: availabilityColor(50) }}
          />
          <span
            className="h-2.5 w-6 rounded-[2px]"
            style={{ backgroundColor: availabilityColor(100) }}
          />
          <span>100 %</span>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <div style={{ minWidth: 170 + dates.length * (cellWidth + 2) }}>
          <div
            className="grid items-center gap-[2px]"
            style={{
              gridTemplateColumns: `160px repeat(${dates.length}, ${cellWidth}px)`,
            }}
          >
            <span />
            {dates.map((date, index) => (
              <span
                key={`date-${date}`}
                className="text-center text-[9px] font-semibold text-slate-500"
              >
                {index % labelEvery === 0 ? date.slice(8) : ''}
              </span>
            ))}

            {rows.map((row) => (
              <div key={row.deviceId} className="contents">
                <span
                  className="truncate pr-2 text-right text-[11px] font-semibold text-slate-600"
                  title={row.label}
                >
                  {row.label}
                </span>
                {row.cells.map((cell, index) => {
                  const style: CSSProperties = {
                    backgroundColor: availabilityColor(cell?.availability_pct ?? null),
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                  };
                  const label = cell
                    ? `${dates[index]} · ${formatAvailability(cell.availability_pct)} · ${formatNumber(cell.updates, 0)} datos${
                        cell.expected !== null
                          ? ` (${formatNumber(cell.expected, 1)} esperados)`
                          : ''
                      }`
                    : `${dates[index]} · sin dato`;
                  return (
                    <span
                      key={`${row.deviceId}-${dates[index]}`}
                      title={label}
                      aria-label={label}
                      className="block h-5 rounded-[2px]"
                      style={style}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="mt-3 text-[11px] text-slate-500">
        Solo dispositivos con latido periódico. Los sensores de eventos no tienen una
        frecuencia esperada.
      </p>
    </section>
  );
}
