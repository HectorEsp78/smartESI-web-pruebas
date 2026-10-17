import { StatCard } from '../ui/StatCard';
import { useEnergyByBuilding } from '../../hooks/useEnergyByBuilding';
import { useOccupancyAirQuality } from '../../hooks/useOccupancyAirQuality';
import { useGas } from '../../hooks/useClimate';
import { useDecisions } from '../../hooks/useDecisions';
import { useGlobalRange } from '../../context/RangeContext';
import { ALL_BUILDINGS } from '../../types/energy';
import { RANGE_LABEL, formatEuro, formatMetricValue, formatNumber, formatPercent } from '../../lib/format';

export function OverviewSection() {
  const { range } = useGlobalRange();
  const { data: energy } = useEnergyByBuilding(range, 'kwh');
  const { data: air } = useOccupancyAirQuality(range, ALL_BUILDINGS);
  const { data: gas } = useGas(range, ALL_BUILDINGS);
  const { data: decisions } = useDecisions(range, ALL_BUILDINGS);

  const topBuilding = energy?.buildings[0] ?? null;
  const rangeLabel = RANGE_LABEL[range].toLowerCase();

  return (
    <div className="space-y-4">
      <p className="max-w-3xl text-sm text-slate-600">
        Panel de estadísticas orientado a la toma de decisiones. Cruza el consumo eléctrico y de gas
        con la ocupación, la temperatura y la calidad del aire de los edificios monitorizados por
        Smart ESI. Todas las gráficas son interactivas: cambia el <strong>periodo</strong> en la
        cabecera y el edificio o la métrica en cada gráfica para explorarlas.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label={`Consumo eléctrico (${rangeLabel})`}
          value={energy ? formatMetricValue(energy.total, energy.unit) : '—'}
          hint="Todos los edificios"
          tone="primary"
        />
        <StatCard
          label="Edificio con mayor consumo"
          value={topBuilding ? topBuilding.label : '—'}
          hint={topBuilding ? `${formatPercent(topBuilding.share * 100, 1)} del total` : undefined}
          tone="accent"
        />
        <StatCard
          label={`Gas (${rangeLabel})`}
          value={gas ? `${formatNumber(gas.stats.total_gas, 0)} kWh` : '—'}
          hint={gas ? `${formatEuro(gas.stats.cost_eur)} · ${formatNumber(gas.stats.total_degree_days, 0)} grados-día` : undefined}
          tone="warning"
        />
        <StatCard
          label="Ahorro potencial al año"
          value={decisions ? formatEuro(decisions.total_savings_eur_year) : '—'}
          hint={decisions ? `${decisions.items.length} oportunidades detectadas` : undefined}
          tone="success"
        />
        <StatCard
          label={`Aire bueno (${rangeLabel})`}
          value={air ? formatPercent(air.stats.good_pct, 0) : '—'}
          hint="Por debajo de 800 ppm de CO₂"
          tone="success"
        />
        <StatCard
          label="CO₂ medio"
          value={air ? `${formatNumber(air.stats.avg_co2, 0)} ppm` : '—'}
          hint={air ? `${formatNumber(air.stats.avg_occupancy, 0)} personas de media` : undefined}
        />
      </div>
    </div>
  );
}
