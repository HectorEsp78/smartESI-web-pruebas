import { EnvironmentFilters } from './EnvironmentFilters';
import { EnvironmentNotes } from './EnvironmentNotes';
import { EnvironmentRoomList } from './EnvironmentRoomList';
import { EnvironmentSummary } from './EnvironmentSummary';
import { useEnvironmentOverview } from '../../../hooks/useEnvironment';
import { useEnvironmentPeriod } from '../../../hooks/useEnvironmentPeriod';
import { environmentPeriodError } from '../../../lib/environment';

export function EnvironmentIndex() {
  const { period, setPeriod } = useEnvironmentPeriod();
  const periodError = environmentPeriodError(period);
  const queryPeriod = periodError ? null : period;
  const { data, isLoading, isFetching, error, retry } = useEnvironmentOverview(queryPeriod);

  return (
    <div className="space-y-5">
      <EnvironmentFilters period={period} onChange={setPeriod} />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-heading text-xl font-semibold text-slate-900">
            Estancias confirmadas
          </h3>
          <p className="text-sm text-muted-foreground">
            {periodError
              ? 'periodo no válido'
              : data
                ? `${data.rooms.length} espacios`
                : 'cargando…'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {isFetching && !isLoading && (
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          )}
          {data && (
            <span className="rounded-sm border border-slate-200 bg-white px-2 py-1 font-semibold">
              {data.data_source === 'mock' ? 'Datos simulados' : 'Datos reales'}
            </span>
          )}
        </div>
      </div>

      {periodError ? (
        <div className="rounded-md border border-dashed border-amber-300 bg-amber-50 p-6 text-sm text-amber-900">
          Corrige el periodo para cargar las estancias.
        </div>
      ) : (
        <>
          <EnvironmentSummary summary={data?.summary ?? null} />
          <EnvironmentRoomList
            rooms={data?.rooms ?? []}
            period={period}
            isLoading={isLoading}
            error={error}
            onRetry={retry}
          />
        </>
      )}

      {data && <EnvironmentNotes notes={data.notes} />}
    </div>
  );
}
