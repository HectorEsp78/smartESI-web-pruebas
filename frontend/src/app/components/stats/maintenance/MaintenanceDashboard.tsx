import { MaintenanceDeviceTable } from './MaintenanceDeviceTable';
import { MaintenanceFilters } from './MaintenanceFilters';
import { MaintenanceHeatmap } from './MaintenanceHeatmap';
import { MaintenanceMatrix } from './MaintenanceMatrix';
import { MaintenanceNotes } from './MaintenanceNotes';
import { MaintenanceOutages } from './MaintenanceOutages';
import { MaintenanceSummary } from './MaintenanceSummary';
import { useMaintenanceOverview } from '../../../hooks/useMaintenance';
import { useMaintenanceDays } from '../../../hooks/useMaintenanceDays';
import { maintenanceDaysLabel } from '../../../lib/maintenance';
import { formatTimestamp } from '../../../lib/format';

function MaintenanceLoading() {
  return (
    <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white py-16">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        Calculando estado de los dispositivos…
      </div>
    </div>
  );
}

export function MaintenanceDashboard() {
  const { days, setDays } = useMaintenanceDays();
  const { data, isLoading, isFetching, error, retry } =
    useMaintenanceOverview(days);

  return (
    <div className="space-y-5">
      <MaintenanceFilters days={days} onChange={setDays} />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-heading text-xl font-semibold text-slate-900">
            Estado de los dispositivos
          </h3>
          <p className="text-sm text-muted-foreground">
            {data
              ? `${data.summary.devices_total} dispositivos · ${maintenanceDaysLabel(days).toLowerCase()}`
              : 'cargando…'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {isFetching && !isLoading && (
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          )}
          {data && (
            <>
              <span className="rounded-sm border border-slate-200 bg-white px-2 py-1 font-semibold">
                {data.data_source === 'mock' ? 'Datos simulados' : 'Datos reales'}
              </span>
              <span className="hidden sm:inline">
                Actualizado {formatTimestamp(data.generated_at, 'd MMM HH:mm')}
              </span>
            </>
          )}
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-4">
          <p className="font-semibold text-destructive">
            No se pudo cargar el estado de mantenimiento.
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
      ) : !data ? (
        <MaintenanceLoading />
      ) : (
        <>
          <MaintenanceSummary summary={data.summary} />

          <div className="grid gap-4 xl:grid-cols-2">
            <MaintenanceMatrix devices={data.devices} />
            <MaintenanceOutages outages={data.outages} />
          </div>

          <MaintenanceDeviceTable devices={data.devices} days={days} />

          <details className="rounded-md border border-slate-200 bg-white px-4 py-3">
            <summary className="cursor-pointer text-sm font-semibold text-slate-700">
              Ver mapa de transmisión diaria (avanzado)
            </summary>
            <div className="mt-3">
              <MaintenanceHeatmap devices={data.devices} cells={data.heatmap} />
            </div>
          </details>

          <MaintenanceNotes notes={data.notes} />
        </>
      )}
    </div>
  );
}
