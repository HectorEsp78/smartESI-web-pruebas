import {
  MATRIX_BG_CLASS,
  maintenanceMatrixCounts,
} from '../../../lib/maintenance';
import { MATRIX_CATEGORY_LABEL } from '../../../types/maintenance';
import type {
  MaintenanceDeviceSummaryDto,
  MatrixCategory,
} from '../../../types/maintenance';

interface MaintenanceMatrixProps {
  devices: MaintenanceDeviceSummaryDto[];
}

interface MatrixCell {
  count: number;
  category: MatrixCategory;
}

interface MatrixRow {
  label: string;
  cells: [MatrixCell, MatrixCell];
}

function cellContent(cell: MatrixCell): string {
  if (cell.count === 0) return '0';
  return `${cell.count} · ${MATRIX_CATEGORY_LABEL[cell.category]}`;
}

export function MaintenanceMatrix({ devices }: MaintenanceMatrixProps) {
  const counts = maintenanceMatrixCounts(devices);
  const rows: MatrixRow[] = [
    {
      label: 'Batería OK',
      cells: [
        { count: counts.ok_ok, category: 'correcto' },
        { count: counts.ok_no_data, category: 'revisar_dispositivo' },
      ],
    },
    {
      label: 'Batería baja',
      cells: [
        { count: counts.low_ok, category: 'cambiar_bateria' },
        { count: counts.low_no_data, category: 'bateria_y_dispositivo' },
      ],
    },
    {
      label: 'Batería sin lectura',
      cells: [
        { count: counts.unknown_ok, category: 'sin_lectura_bateria' },
        { count: counts.unknown_no_data, category: 'revisar_sin_datos' },
      ],
    },
  ];

  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Cruce batería × transmisión
          </h3>
          <p className="text-xs text-muted-foreground">
            La decisión cambia según la batería y si el dispositivo sigue enviando datos.
          </p>
        </div>
        <p className="text-xs text-slate-500">
          {counts.wired_total} dispositivos de red · {counts.wired_no_data} sin datos
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <div className="min-w-[620px]">
          <div className="grid grid-cols-[150px_repeat(2,minmax(0,1fr))] gap-2">
            <span />
            <span className="px-2 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
              Datos OK
            </span>
            <span className="px-2 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
              Sin datos
            </span>

            {rows.map((row) => (
              <div key={row.label} className="contents">
                <span className="flex items-center text-xs font-semibold text-slate-700">
                  {row.label}
                </span>
                {row.cells.map((cell, index) => (
                  <div
                    key={`${row.label}-${index}`}
                    className={`rounded-sm border px-3 py-2 text-xs font-semibold ${MATRIX_BG_CLASS[cell.category]}`}
                  >
                    {cellContent(cell)}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="mt-3 text-[11px] text-slate-500">
        Batería baja incluye nivel crítico y bajo. Los dispositivos sin batería se evalúan
        solo por transmisión.
      </p>
    </section>
  );
}
