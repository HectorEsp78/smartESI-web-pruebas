import { WeatherAemetCross } from './WeatherAemetCross';
import {
  WeatherHumidityChart,
  WeatherPmChart,
  WeatherPressureChart,
  WeatherTemperatureChart,
} from './WeatherCharts';
import { WeatherCurrent } from './WeatherCurrent';
import { WeatherDailyTable } from './WeatherDailyTable';
import { WeatherEnergyCross } from './WeatherEnergyCross';
import { WeatherFilters } from './WeatherFilters';
import { WeatherIndoorCross } from './WeatherIndoorCross';
import { WeatherNotes } from './WeatherNotes';
import { WeatherPmCross } from './WeatherPmCross';
import { WeatherSummary } from './WeatherSummary';
import { useWeatherOverview } from '../../../hooks/useWeather';
import { useWeatherDays } from '../../../hooks/useWeatherDays';
import { weatherDaysLabel } from '../../../lib/weather';
import { formatTimestamp } from '../../../lib/format';

function WeatherLoading() {
  return (
    <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white py-16">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        Calculando datos de la estación meteorológica…
      </div>
    </div>
  );
}

export function WeatherDashboard() {
  const { days, setDays } = useWeatherDays();
  const { data, isLoading, isFetching, error, retry } =
    useWeatherOverview(days);

  return (
    <div className="space-y-5">
      <WeatherFilters days={days} onChange={setDays} />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-heading text-xl font-semibold text-slate-900">
            Estación meteorológica
          </h3>
          <p className="text-sm text-muted-foreground">
            {data
              ? `${weatherDaysLabel(days).toLowerCase()} · ${data.summary.samples} lecturas`
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
            No se pudo cargar la estación meteorológica.
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
        <WeatherLoading />
      ) : (
        <>
          <WeatherCurrent current={data.current} />
          <WeatherSummary summary={data.summary} />

          <div className="grid gap-4 xl:grid-cols-2">
            <WeatherTemperatureChart
              series={data.series}
              granularity={data.granularity}
              isLoading={isLoading}
              error={error}
              retry={retry}
            />
            <WeatherHumidityChart
              series={data.series}
              granularity={data.granularity}
              isLoading={isLoading}
              error={error}
              retry={retry}
            />
            <WeatherPressureChart
              series={data.series}
              granularity={data.granularity}
              isLoading={isLoading}
              error={error}
              retry={retry}
            />
            <WeatherPmChart
              series={data.series}
              granularity={data.granularity}
              isLoading={isLoading}
              error={error}
              retry={retry}
            />
          </div>

          <div className="space-y-3">
            <div>
              <h3 className="font-heading text-xl font-semibold text-slate-900">
                Análisis cruzado
              </h3>
              <p className="text-sm text-muted-foreground">
                Exterior, interior, AEMET y consumo energético.
              </p>
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              <WeatherIndoorCross cross={data.indoor_cross} />
              <WeatherAemetCross cross={data.aemet_cross} />
              <WeatherEnergyCross cross={data.energy_cross} />
              <WeatherPmCross cross={data.pm_cross} />
            </div>
          </div>

          <details className="rounded-md border border-slate-200 bg-white px-4 py-3">
            <summary className="cursor-pointer text-sm font-semibold text-slate-700">
              Ver resumen diario (avanzado)
            </summary>
            <div className="mt-3">
              <WeatherDailyTable daily={data.daily} />
            </div>
          </details>

          <WeatherNotes notes={data.notes} />
        </>
      )}
    </div>
  );
}
