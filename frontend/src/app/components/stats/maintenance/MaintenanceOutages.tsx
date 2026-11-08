import {
  OUTAGE_SCOPE_BG_CLASS,
  formatDateRange,
  formatDurationHours,
} from '../../../lib/maintenance';
import { OUTAGE_SCOPE_LABEL } from '../../../types/maintenance';
import type { MaintenanceOutageDto } from '../../../types/maintenance';

interface MaintenanceOutagesProps {
  outages: MaintenanceOutageDto[];
}

export function MaintenanceOutages({ outages }: MaintenanceOutagesProps) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">
            Cortes correlacionados
          </h3>
          <p className="text-xs text-muted-foreground">
            Caídas que afectan a varios dispositivos a la vez; no se cuentan como
            averías individuales.
          </p>
        </div>
        <span className="rounded-sm border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-600">
          {outages.length} {outages.length === 1 ? 'corte' : 'cortes'}
        </span>
      </div>

      {outages.length === 0 ? (
        <p className="mt-4 rounded-sm border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm text-slate-500">
          Sin cortes globales o de grupo en el periodo.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
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
                <span className="text-xs text-slate-500">
                  {outage.device_count} dispositivos
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
      )}
    </section>
  );
}
