import { formatNumber, formatTimestamp } from '../../../lib/format';
import type { WeatherDailyPointDto } from '../../../types/weather';

interface WeatherDailyTableProps {
  daily: WeatherDailyPointDto[];
}

function value(value: number | null, digits = 1, unit = ''): string {
  if (value === null) return '—';
  return `${formatNumber(value, digits)}${unit ? ` ${unit}` : ''}`;
}

export function WeatherDailyTable({ daily }: WeatherDailyTableProps) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-4">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Resumen diario
        </h3>
        <p className="text-xs text-muted-foreground">
          Mínimos, medias y máximos por día, con la cobertura de la estación.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-500">
              <th className="py-2 pr-3 font-semibold">Día</th>
              <th className="py-2 pr-3 font-semibold">Cobertura</th>
              <th className="py-2 pr-3 font-semibold">Temp. mín / med / máx</th>
              <th className="py-2 pr-3 font-semibold">Humedad</th>
              <th className="py-2 pr-3 font-semibold">Presión</th>
              <th className="py-2 pr-3 font-semibold">PM2.5 med / máx</th>
              <th className="py-2 pr-3 font-semibold">Interior</th>
              <th className="py-2 pr-3 font-semibold">Gas</th>
              <th className="py-2 pr-3 font-semibold">Electricidad</th>
              <th className="py-2 font-semibold">HDD / CDD</th>
            </tr>
          </thead>
          <tbody>
            {daily.map((point) => {
              const empty = point.samples === 0;
              return (
                <tr
                  key={point.date}
                  className={`border-b border-slate-100 ${empty ? 'text-slate-400' : 'text-slate-700'}`}
                >
                  <td className="whitespace-nowrap py-2 pr-3 font-semibold">
                    {formatTimestamp(`${point.date}T00:00:00`, 'EEE d MMM')}
                  </td>
                  <td className="py-2 pr-3">
                    {point.coverage_pct === null
                      ? '—'
                      : `${formatNumber(point.coverage_pct, 0)} %`}
                    <span className="ml-1 text-slate-400">
                      ({point.samples})
                    </span>
                  </td>
                  <td className="py-2 pr-3">
                    {value(point.temperature_min_c)} /{' '}
                    {value(point.temperature_avg_c)} /{' '}
                    {value(point.temperature_max_c)}
                  </td>
                  <td className="py-2 pr-3">{value(point.humidity_avg_pct, 1, '%')}</td>
                  <td className="py-2 pr-3">{value(point.pressure_avg_hpa, 1, 'hPa')}</td>
                  <td className="py-2 pr-3">
                    {value(point.pm25_avg, 0)} / {value(point.pm25_max, 0)}
                  </td>
                  <td className="py-2 pr-3">
                    {value(point.indoor_temperature_avg_c, 1, '°C')}
                  </td>
                  <td className="py-2 pr-3">{value(point.gas_m3, 2, 'm³')}</td>
                  <td className="py-2 pr-3">
                    {value(point.electricity_kwh, 1, 'kWh')}
                  </td>
                  <td className="py-2">
                    {value(point.heating_degree_days, 1)} /{' '}
                    {value(point.cooling_degree_days, 1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
