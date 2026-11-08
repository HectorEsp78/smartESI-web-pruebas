import {
  formatCo2,
  formatOccupancy,
  formatTemperature,
} from '../../../lib/environment';
import type { EnvironmentSummaryDto } from '../../../types/environment';

interface EnvironmentSummaryProps {
  summary: EnvironmentSummaryDto | null;
}

export function EnvironmentSummary({ summary }: EnvironmentSummaryProps) {
  const items = [
    {
      label: 'Temperatura media',
      value: formatTemperature(summary?.avg_temperature_c ?? null),
      hint: 'Estancias con sensor',
    },
    {
      label: 'CO₂ medio',
      value: formatCo2(summary?.avg_co2_ppm ?? null),
      hint:
        summary && summary.rooms_with_co2 > 0
          ? `${summary.co2_alert_rooms} por encima de 800 ppm`
          : 'Sin sensores de CO₂',
    },
    {
      label: 'Ocupación media',
      value: formatOccupancy(summary?.occupancy_pct ?? null),
      hint: 'Periodo seleccionado',
    },
    {
      label: 'Ocupadas ahora',
      value: summary ? `${summary.occupied_now} / ${summary.rooms_with_presence}` : '—',
      hint: 'Último estado de presencia',
    },
  ];

  return (
    <dl className="grid gap-4 rounded-md border border-slate-200 bg-white p-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <div key={item.label}>
          <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
            {item.label}
          </dt>
          <dd className="mt-1 font-heading text-xl font-bold text-slate-900">{item.value}</dd>
          <p className="mt-0.5 text-[11px] text-slate-500">{item.hint}</p>
        </div>
      ))}
    </dl>
  );
}
