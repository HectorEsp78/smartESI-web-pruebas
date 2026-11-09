import { EnvironmentRangeSelector } from './EnvironmentRangeSelector';
import { EnvironmentRoomCard } from './EnvironmentRoomCard';
import { INFRASTRUCTURE_ROOM_IDS, getRoomCardMetadata } from './roomCardMetadata';
import { useEnvironmentOverview } from '../../../hooks/useEnvironment';
import { useEnvironmentPeriod } from '../../../hooks/useEnvironmentPeriod';
import { environmentPeriodError } from '../../../lib/environment';

export function EnvironmentIndex() {
  const { period, setPeriod } = useEnvironmentPeriod();
  const periodError = environmentPeriodError(period);
  const queryPeriod = periodError ? null : period;
  const { data, isLoading, isFetching, error, retry } = useEnvironmentOverview(queryPeriod);

  const roomOrder: readonly string[] = INFRASTRUCTURE_ROOM_IDS;
  const rooms = [...(data?.rooms ?? [])]
    .filter((room) => roomOrder.includes(room.room_id))
    .sort((a, b) => roomOrder.indexOf(a.room_id) - roomOrder.indexOf(b.room_id));

  return (
    <div className="mt-5 space-y-5">
      <EnvironmentRangeSelector period={period} onChange={setPeriod} />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-heading text-xl font-semibold text-slate-900">
            Aulas monitorizadas
          </h3>
          <p className="text-sm text-muted-foreground">
            Temperatura, humedad y presencia en tiempo real
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
          {periodError} Elige otro periodo para cargar las aulas.
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-6">
          <p className="font-semibold text-destructive">No se pudieron cargar las aulas.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            Reintentar
          </button>
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-5 pb-2 xl:grid-cols-2">
          {INFRASTRUCTURE_ROOM_IDS.map((roomId) => {
            const metadata = getRoomCardMetadata(roomId);
            return (
              <div
                key={roomId}
                className="flex h-40 animate-pulse overflow-hidden rounded-lg border border-slate-200 bg-white"
              >
                <div className="w-28 shrink-0 bg-slate-200 sm:w-40 lg:w-44" />
                <div className="flex flex-1 flex-col gap-3 p-4">
                  <div className="h-3 w-16 rounded bg-slate-200" />
                  <div className="h-5 w-24 rounded bg-slate-200" />
                  <div className="h-3 w-32 rounded bg-slate-100" />
                  <div className="mt-auto grid grid-cols-3 gap-2">
                    <div className="h-10 rounded bg-slate-100" />
                    <div className="h-10 rounded bg-slate-100" />
                    <div className="h-10 rounded bg-slate-100" />
                  </div>
                  <span className="sr-only">{metadata?.imageAlt ?? roomId}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : rooms.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-muted-foreground">
          No hay aulas disponibles para el periodo seleccionado.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 pb-2 xl:grid-cols-2">
          {rooms.map((room) => (
            <EnvironmentRoomCard key={room.room_id} room={room} period={period} />
          ))}
        </div>
      )}
    </div>
  );
}
