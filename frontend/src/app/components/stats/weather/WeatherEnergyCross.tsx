import { WeatherMetric } from './WeatherMetric';
import { formatEuro, formatNumber } from '../../../lib/format';
import { formatCorrelation } from '../../../lib/weather';
import type { WeatherEnergyCrossDto } from '../../../types/weather';

interface WeatherEnergyCrossProps {
  cross: WeatherEnergyCrossDto;
}

export function WeatherEnergyCross({ cross }: WeatherEnergyCrossProps) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-4">
        <h3 className="font-heading text-lg font-semibold text-slate-900">
          Temperatura vs. energía
        </h3>
        <p className="text-xs text-muted-foreground">
          Grados-día de calefacción y refrigeración frente al gas y la electricidad.
        </p>
      </div>

      {!cross.available ? (
        <p className="py-6 text-sm text-slate-500">
          No hay datos energéticos suficientes para cruzar con la temperatura.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <WeatherMetric
              label="Gas del edificio"
              value={
                cross.gas_m3 === null
                  ? '—'
                  : `${formatNumber(cross.gas_m3, 1)} m³`
              }
              hint={`Coste: ${cross.gas_cost_eur === null ? '—' : formatEuro(cross.gas_cost_eur, 2)}`}
              tone="primary"
            />
            <WeatherMetric
              label="Electricidad del cuadro"
              value={
                cross.electricity_kwh === null
                  ? '—'
                  : `${formatNumber(cross.electricity_kwh, 0)} kWh`
              }
              hint={`${cross.days} días analizados · ${cross.excluded_days} excluidos`}
              tone="primary"
            />
            <WeatherMetric
              label="Grados-día"
              value={`${cross.heating_degree_days === null ? '—' : formatNumber(cross.heating_degree_days, 1)} HDD`}
              hint={`${cross.cooling_degree_days === null ? '—' : formatNumber(cross.cooling_degree_days, 1)} CDD · bases 18 / 22 °C`}
              tone="neutral"
            />
            <WeatherMetric
              label="Gas por grado-día"
              value={
                cross.gas_per_degree_day === null
                  ? '—'
                  : `${formatNumber(cross.gas_per_degree_day, 2)} m³/HDD`
              }
              hint="Orientativo; el gas puede incluir otros usos"
              tone="accent"
            />
            <WeatherMetric
              label="Correlación temperatura–gas"
              value={formatCorrelation(cross.temperature_gas_correlation)}
              hint="Negativa: más frío, más consumo"
              tone="neutral"
            />
            <WeatherMetric
              label="Correlación HDD–gas"
              value={formatCorrelation(cross.heating_degree_gas_correlation)}
              hint="Relación con la demanda de calefacción"
              tone="neutral"
            />
            <WeatherMetric
              label="Correlación temperatura–electricidad"
              value={formatCorrelation(cross.temperature_electricity_correlation)}
              hint="Incluye climatización y carga base"
              tone="neutral"
            />
            <WeatherMetric
              label="Electricidad por CDD"
              value={
                cross.electricity_per_degree_day === null
                  ? '—'
                  : `${formatNumber(cross.electricity_per_degree_day, 0)} kWh/CDD`
              }
              hint="Solo se muestra con suficientes días de refrigeración"
              tone="neutral"
            />
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Se excluyen los días con saltos anómalos de los contadores de energía.
            El gas es del edificio y la electricidad del cuadro general.
          </p>
        </>
      )}
    </div>
  );
}
