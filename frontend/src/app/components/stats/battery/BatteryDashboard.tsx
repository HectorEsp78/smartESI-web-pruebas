import { useState } from 'react';
import { NavLink, Navigate, useParams } from 'react-router';
import { BatteryHistoryDialog } from './BatteryHistoryDialog';
import { BatterySensorCard } from './BatterySensorCard';
import { StatCard } from '../../ui/StatCard';
import { useBatteryGroup } from '../../../hooks/useBattery';
import { formatTimestamp } from '../../../lib/format';
import { BATTERY_GROUP_PAGES, DEFAULT_BATTERY_GROUP, isBatteryGroupId } from '../../../lib/battery';
import type { BatterySensorDto } from '../../../types/battery';

function BatteryGroupPage({ groupId }: { groupId: string }) {
  const { data, isFetching, isLoading, error, retry } = useBatteryGroup(groupId);
  const [selected, setSelected] = useState<BatterySensorDto | null>(null);
  const page = BATTERY_GROUP_PAGES.find((candidate) => candidate.id === groupId);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-heading text-xl font-semibold text-slate-900">{page?.label}</h3>
          <p className="text-sm text-muted-foreground">
            {page?.description} Pulsa una tarjeta para ver su histórico.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          {isFetching && !isLoading && (
            <span
              className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent"
              aria-label="Actualizando"
            />
          )}
          {data && (
            <>
              <span className="rounded-sm border border-slate-200 bg-white px-2 py-1 font-semibold">
                {data.data_source === 'mock' ? 'Datos simulados' : 'Datos reales'}
              </span>
              <span>Actualizado {formatTimestamp(data.generated_at, 'd MMM HH:mm')}</span>
            </>
          )}
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-5">
          <p className="font-semibold text-destructive">No se pudieron cargar las baterías.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-4 cursor-pointer rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Reintentar
          </button>
        </div>
      ) : !data ? (
        <div className="flex items-center justify-center gap-3 rounded-md border border-slate-200 bg-white py-16 text-sm text-slate-500">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          Cargando baterías…
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Sensores" value={String(data.summary.total)} />
            <StatCard
              label="Batería baja o crítica"
              value={String(data.summary.low + data.summary.critical)}
              hint={`${data.summary.critical} en nivel crítico`}
              tone={data.summary.low + data.summary.critical > 0 ? 'warning' : 'neutral'}
            />
            <StatCard
              label="Sin lectura actual"
              value={String(data.summary.without_current_reading)}
              hint="Último dato no válido o de hace más de 7 días"
            />
          </div>

          {data.summary.without_current_reading > 0 && (
            <p className="rounded-sm border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              En los sensores sin lectura actual se muestra el último valor válido con su fecha: no
              indica su nivel de hoy.
            </p>
          )}
          {data.unit === 'millivolt' && (
            <p className="text-sm text-slate-600">
              Estos sensores miden el voltaje de la pila. El porcentaje es una estimación y llega al
              100 % a partir de 3600 mV.
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {data.sensors.map((sensor) => (
              <BatterySensorCard key={sensor.id} sensor={sensor} onSelect={setSelected} />
            ))}
          </div>
        </>
      )}

      {selected && (
        <BatteryHistoryDialog
          key={selected.id}
          groupId={groupId}
          sensor={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

export function BatteryDashboard() {
  const { groupId } = useParams();

  if (!isBatteryGroupId(groupId)) {
    return <Navigate to={`/mantenimiento/${DEFAULT_BATTERY_GROUP}`} replace />;
  }

  return (
    <div className="space-y-5">
      <nav aria-label="Secciones de Mantenimiento" className="flex flex-wrap gap-2">
        {BATTERY_GROUP_PAGES.map((page) => (
          <NavLink
            key={page.id}
            to={`/mantenimiento/${page.id}`}
            className={({ isActive }) =>
              `rounded-sm border px-4 py-2 text-sm font-semibold transition-colors ${
                isActive
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-slate-300 bg-white text-slate-700 hover:border-primary hover:text-primary'
              }`
            }
          >
            {page.label}
          </NavLink>
        ))}
      </nav>

      <BatteryGroupPage key={groupId} groupId={groupId} />
    </div>
  );
}
