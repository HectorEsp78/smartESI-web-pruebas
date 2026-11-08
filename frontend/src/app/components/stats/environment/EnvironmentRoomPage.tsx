import { Link } from 'react-router';
import type { ReactNode } from 'react';
import { EnvironmentBenchmarkCard } from './EnvironmentBenchmarkCard';
import { EnvironmentCo2OccupancyCard } from './EnvironmentCo2OccupancyCard';
import { EnvironmentFilters } from './EnvironmentFilters';
import { EnvironmentGasContextChart } from './EnvironmentGasContextChart';
import { EnvironmentHeatmap } from './EnvironmentHeatmap';
import { EnvironmentNotes } from './EnvironmentNotes';
import {
  EnvironmentRoomHumidityChart,
  EnvironmentRoomTemperatureChart,
} from './EnvironmentRoomClimateCharts';
import { EnvironmentRoomCo2Chart } from './EnvironmentRoomCo2Chart';
import { EnvironmentRoomHeader } from './EnvironmentRoomHeader';
import { EnvironmentRoomStats } from './EnvironmentRoomStats';
import { EnvironmentThermalRecoveryCard } from './EnvironmentThermalRecoveryCard';
import { useEnvironmentRoom } from '../../../hooks/useEnvironment';
import { useEnvironmentPeriod } from '../../../hooks/useEnvironmentPeriod';
import { environmentPeriodError } from '../../../lib/environment';
import type { DatePeriod } from '../../../lib/electricity';

interface EnvironmentRoomPageProps {
  roomId: string;
}

function indexHref(period: DatePeriod): string {
  const params = new URLSearchParams({ start: period.start, end: period.end });
  return `/infraestructura?${params.toString()}`;
}

function granularityLabel(granularity: 'hour' | 'day' | 'week'): string {
  if (granularity === 'hour') return 'Agregación horaria';
  if (granularity === 'day') return 'Agregación diaria';
  return 'Agregación semanal';
}

function AdvancedAnalysis({ children }: { children: ReactNode }) {
  return (
    <details className="rounded-md border border-slate-200 bg-white">
      <summary className="cursor-pointer px-4 py-3">
        <span className="font-heading text-base font-semibold text-slate-900">
          Análisis avanzado
        </span>
        <span className="ml-2 text-xs text-slate-500">
          Humedad, mapas, cruces, comparativa y gas
        </span>
      </summary>
      <div className="space-y-6 border-t border-slate-200 p-4 sm:p-5">{children}</div>
    </details>
  );
}

export function EnvironmentRoomPage({ roomId }: EnvironmentRoomPageProps) {
  const { period, setPeriod } = useEnvironmentPeriod();
  const periodError = environmentPeriodError(period);
  const queryPeriod = periodError ? null : period;
  const { data, isLoading, error, retry } = useEnvironmentRoom(roomId, queryPeriod);

  if (periodError) {
    return (
      <div className="space-y-5">
        <EnvironmentFilters period={period} onChange={setPeriod} />
        <div className="rounded-md border border-dashed border-amber-300 bg-amber-50 p-6 text-sm text-amber-900">
          Corrige el periodo para cargar la estancia.
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-5">
        <EnvironmentFilters period={period} onChange={setPeriod} />
        <div className="rounded-md border border-destructive/35 bg-white p-6">
          <p className="font-semibold text-destructive">No se pudo cargar la estancia.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={retry}
              className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              Reintentar
            </button>
            <Link
              to={indexHref(period)}
              className="rounded-sm border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              Volver a las estancias
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!data || isLoading) {
    return (
      <div className="space-y-5">
        <EnvironmentFilters period={period} onChange={setPeriod} />
        <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white py-20">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  const { room, benchmark, context, series, heatmap, co2_occupancy, thermal_recovery } = data;
  const hasCo2 = room.has_co2;
  const hasPresence = room.has_presence;

  return (
    <div className="space-y-5">
      <EnvironmentFilters period={period} onChange={setPeriod} />
      <EnvironmentRoomHeader room={room} period={period} dataSource={data.data_source} />

      <section className="space-y-4">
        <div>
          <h3 className="font-heading text-lg font-semibold text-slate-900">Resumen del periodo</h3>
          <p className="text-xs text-muted-foreground">{granularityLabel(data.granularity)}</p>
        </div>
        <EnvironmentRoomStats room={room} />
      </section>

      {room.has_temperature && (
        <EnvironmentRoomTemperatureChart
          series={series}
          granularity={data.granularity}
          isLoading={false}
          error={null}
          retry={retry}
        />
      )}

      {hasCo2 && (
        <EnvironmentRoomCo2Chart
          series={series}
          granularity={data.granularity}
          isLoading={false}
          error={null}
          retry={retry}
        />
      )}

      <AdvancedAnalysis>
        {room.has_humidity && (
          <EnvironmentRoomHumidityChart
            series={series}
            granularity={data.granularity}
            isLoading={false}
            error={null}
            retry={retry}
          />
        )}

        {hasPresence && (
          <div className="grid gap-4 xl:grid-cols-2">
            <EnvironmentHeatmap
              cells={heatmap}
              metric="presence"
              isLoading={false}
              error={null}
              retry={retry}
            />
            {hasCo2 && (
              <EnvironmentHeatmap
                cells={heatmap}
                metric="co2"
                isLoading={false}
                error={null}
                retry={retry}
              />
            )}
          </div>
        )}

        {hasCo2 && hasPresence && (
          <EnvironmentCo2OccupancyCard
            points={series}
            stats={co2_occupancy}
            isLoading={false}
            error={null}
            retry={retry}
          />
        )}

        {room.has_temperature && hasPresence && (
          <EnvironmentThermalRecoveryCard recovery={thermal_recovery} />
        )}

        <EnvironmentBenchmarkCard room={room} benchmark={benchmark} />

        {room.has_temperature && (
          <EnvironmentGasContextChart
            series={series}
            context={context}
            granularity={data.granularity}
            isLoading={false}
            error={null}
            retry={retry}
          />
        )}
      </AdvancedAnalysis>

      <EnvironmentNotes notes={data.notes} />
    </div>
  );
}
