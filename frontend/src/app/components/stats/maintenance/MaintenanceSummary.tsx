import { StatCard } from '../../ui/StatCard';
import { formatAvailability } from '../../../lib/maintenance';
import type { MaintenanceSummaryDto } from '../../../types/maintenance';

interface MaintenanceSummaryProps {
  summary: MaintenanceSummaryDto;
}

export function MaintenanceSummary({ summary }: MaintenanceSummaryProps) {
  const lowTone = summary.critical_battery > 0 ? 'warning' : 'neutral';

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <StatCard
        label="Baterías bajas"
        value={`${summary.low_battery} / ${summary.with_battery}`}
        hint={`${summary.critical_battery} en nivel crítico`}
        tone={lowTone}
      />
      <StatCard
        label="Dispositivos sin datos"
        value={`${summary.no_data} / ${summary.devices_total}`}
        hint={`${summary.devices_periodic} periódicos · ${summary.devices_event} por eventos`}
        tone={summary.no_data > 0 ? 'warning' : 'success'}
      />
      <StatCard
        label="Cortes correlacionados"
        value={`${summary.global_outages}`}
        hint={`${summary.group_outages} de grupo · ${summary.individual_outages} individuales`}
        tone="primary"
      />
      <StatCard
        label="Disponibilidad media"
        value={formatAvailability(summary.avg_availability_pct)}
        hint="Sin contar cortes globales"
        tone={
          summary.avg_availability_pct !== null && summary.avg_availability_pct < 90
            ? 'warning'
            : 'success'
        }
      />
      <StatCard
        label="Cambios de batería"
        value={`${summary.replacements_detected}`}
        hint="Detectados en el periodo"
        tone="primary"
      />
      <StatCard
        label="Cambio previsto ≤30 d"
        value={`${summary.forecast_replace_30d}`}
        hint={`≤60 d: ${summary.forecast_replace_60d} · ≤90 d: ${summary.forecast_replace_90d}`}
        tone={summary.forecast_replace_30d > 0 ? 'warning' : 'neutral'}
      />
    </div>
  );
}
