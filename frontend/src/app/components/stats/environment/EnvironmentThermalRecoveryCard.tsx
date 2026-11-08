import { StatCard } from '../../ui/StatCard';
import { formatNumber } from '../../../lib/format';
import { formatRecoveryHours, formatTemperature } from '../../../lib/environment';
import type { EnvironmentThermalRecoveryDto } from '../../../types/environment';

interface Props {
  recovery: EnvironmentThermalRecoveryDto;
}

export function EnvironmentThermalRecoveryCard({ recovery }: Props) {
  const hasTransitions = recovery.transitions > 0;

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <div className="mb-4 border-b border-slate-200 pb-3">
        <h3 className="font-heading text-lg font-semibold text-slate-900">Recuperación térmica</h3>
        <p className="text-xs text-muted-foreground">
          Tiempo que tarda la estancia en volver a su temperatura de reposo después de
          desocuparse.
        </p>
      </div>

      {!hasTransitions ? (
        <p className="py-6 text-center text-sm text-slate-500">
          No hay transiciones de ocupado a vacío suficientes para calcular la recuperación
          térmica.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Temperatura de reposo"
            value={formatTemperature(recovery.baseline_temperature_c)}
            hint="Mediana de las horas sin presencia"
          />
          <StatCard
            label="Recuperación mediana"
            value={formatRecoveryHours(recovery.median_recovery_hours)}
            hint={`${recovery.transitions} transiciones analizadas`}
            tone="primary"
          />
          <StatCard
            label="Cambio en la 1.ª hora"
            value={
              recovery.median_change_per_hour_c === null
                ? '—'
                : `${formatNumber(recovery.median_change_per_hour_c, 1)} °C/h`
            }
            hint="Cambio medio de temperatura en la primera hora sin presencia"
            tone={
              recovery.median_change_per_hour_c !== null &&
              recovery.median_change_per_hour_c < 0
                ? 'success'
                : 'neutral'
            }
          />
          <StatCard
            label="Sin recuperar en 6 h"
            value={`${recovery.no_recovery_count} / ${recovery.transitions}`}
            hint="Transiciones que no vuelven a la temperatura de reposo en 6 horas"
            tone={recovery.no_recovery_count > 0 ? 'warning' : 'success'}
          />
        </div>
      )}
    </section>
  );
}
