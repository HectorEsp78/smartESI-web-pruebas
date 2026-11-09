import { WeatherAemetNotice } from './WeatherAemetNotice';
import {
  WeatherBatteryChart,
  WeatherHourlyBiasChart,
  WeatherHumidityChart,
  WeatherPmChart,
  WeatherPressureChart,
  WeatherRainChart,
  WeatherTemperatureChart,
} from './WeatherCharts';
import { WeatherComparison } from './WeatherComparison';
import { WeatherCurrent } from './WeatherCurrent';
import { WeatherFilters } from './WeatherFilters';
import { WeatherNotes } from './WeatherNotes';
import { WeatherSummary } from './WeatherSummary';
import { ExportCsvButton } from '../../ui/ExportCsvButton';
import { useDatePeriod } from '../../../hooks/useDatePeriod';
import { useWeatherOverview } from '../../../hooks/useWeather';
import { formatTimestamp } from '../../../lib/format';
import { DEFAULT_WEATHER_PERIOD_DAYS, weatherPeriodError } from '../../../lib/weather';
import type { WeatherOverviewDto } from '../../../types/weather';

const CSV_HEADERS = [
  'Fecha',
  'Temperatura estación (°C)',
  'Temperatura AEMET (°C)',
  'Humedad estación (%)',
  'Humedad AEMET (%)',
  'Presión estación (hPa)',
  'Presión AEMET (hPa)',
  'Lluvia AEMET (mm)',
  'PM1 (índice)',
  'PM2.5 (índice)',
  'PM10 (índice)',
  'Batería (%)',
];

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h3 className="font-heading text-xl font-semibold text-slate-900">{title}</h3>
      <p className="text-sm text-muted-foreground">{subtitle}</p>
    </div>
  );
}

function csvRows(data: WeatherOverviewDto) {
  const pattern = data.granularity === 'hour' ? 'yyyy-MM-dd HH:mm' : 'yyyy-MM-dd';
  return data.series.map((point) => [
    formatTimestamp(point.timestamp, pattern),
    point.station_temperature_c,
    point.aemet_temperature_c,
    point.station_humidity_pct,
    point.aemet_humidity_pct,
    point.station_pressure_hpa,
    point.aemet_pressure_hpa,
    point.aemet_precipitation_mm,
    point.pm1,
    point.pm25,
    point.pm10,
    point.battery_pct,
  ]);
}

function WeatherContent({ data }: { data: WeatherOverviewDto }) {
  const chartProps = { series: data.series, granularity: data.granularity };

  return (
    <>
      <WeatherAemetNotice availability={data.aemet_availability} latest={data.aemet_latest} />

      {data.aemet_availability.coverage !== 'none' && (
        <section className="space-y-3">
          <SectionTitle
            title="Estación frente a AEMET"
            subtitle="Solo con las horas en las que hay datos de ambas fuentes."
          />
          <WeatherComparison comparison={data.comparison} />
        </section>
      )}

      <section className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <SectionTitle
            title="Evolución en el periodo"
            subtitle={data.granularity === 'hour' ? 'Medias por hora' : 'Medias por día'}
          />
          <ExportCsvButton
            filename="medio-ambiente-estacion-aemet.csv"
            headers={CSV_HEADERS}
            rows={csvRows(data)}
          />
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <WeatherTemperatureChart {...chartProps} />
          <WeatherHourlyBiasChart hourlyBias={data.comparison.hourly_bias} />
          <WeatherHumidityChart {...chartProps} />
          <WeatherPressureChart {...chartProps} />
          <WeatherRainChart {...chartProps} />
          <WeatherPmChart {...chartProps} />
          <WeatherBatteryChart {...chartProps} />
        </div>
      </section>

      <section className="space-y-3">
        <SectionTitle
          title="Resumen del periodo"
          subtitle="Estadísticas de la estación y lluvia registrada por AEMET."
        />
        <WeatherSummary summary={data.summary} />
      </section>

      <WeatherNotes notes={data.notes} />
    </>
  );
}

export function WeatherDashboard() {
  const { period, setPeriod } = useDatePeriod(DEFAULT_WEATHER_PERIOD_DAYS);
  const periodError = weatherPeriodError(period);
  const { data, isFetching, isLoading, error, retry } = useWeatherOverview(
    periodError ? null : period,
  );

  return (
    <div className="space-y-5">
      <WeatherFilters period={period} error={periodError} onChange={setPeriod} />

      <div className="flex flex-wrap items-center justify-end gap-2 text-xs text-slate-500">
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

      {data && <WeatherCurrent current={data.current} aemet={data.aemet_latest} />}

      {periodError ? null : error ? (
        <div className="rounded-md border border-destructive/35 bg-white p-5">
          <p className="font-semibold text-destructive">No se pudieron cargar los datos.</p>
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
          Comparando la estación con AEMET…
        </div>
      ) : (
        <WeatherContent data={data} />
      )}
    </div>
  );
}
