import { useState } from 'react';
import { ExportCsvButton } from '../../ui/ExportCsvButton';
import { SelectField } from '../../ui/SelectField';
import { StatCard } from '../../ui/StatCard';
import { useBuildings } from '../../../hooks/useBuildings';
import { useDecisions } from '../../../hooks/useDecisions';
import { useGlobalRange } from '../../../context/RangeContext';
import { ALL_BUILDINGS } from '../../../types/energy';
import { formatEuro, formatNumber } from '../../../lib/format';
import type { OpportunityCategory, OpportunityPriority } from '../../../types/decisions';

const CATEGORY_LABEL: Record<OpportunityCategory, string> = {
  iluminacion: 'Iluminación',
  calefaccion: 'Calefacción',
  electricidad: 'Electricidad',
  tendencia: 'Tendencia',
};

const PRIORITY_CLASS: Record<OpportunityPriority, string> = {
  alta: 'bg-accent/10 text-accent',
  media: 'bg-warning/10 text-warning',
  baja: 'bg-slate-200 text-slate-600',
};

const PRIORITY_LABEL: Record<OpportunityPriority, string> = {
  alta: 'Prioridad alta',
  media: 'Prioridad media',
  baja: 'Prioridad baja',
};

export function DecisionsPanel() {
  const { range } = useGlobalRange();
  const [building, setBuilding] = useState<string>(ALL_BUILDINGS);
  const { meta } = useBuildings();
  const { data, isLoading, error, retry } = useDecisions(range, building);

  const buildingOptions = [
    { value: ALL_BUILDINGS, label: 'Todos los edificios' },
    ...(meta?.buildings ?? []).map((item) => ({ value: item.id, label: item.label })),
  ];

  const exportRows = (data?.items ?? []).map((item) => [
    CATEGORY_LABEL[item.category],
    PRIORITY_LABEL[item.priority],
    item.title,
    item.description,
    item.evidence,
    item.metric_value,
    item.metric_unit,
    item.savings_kwh_year,
    item.savings_eur_year,
  ]);

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="font-heading text-lg font-semibold text-slate-900">
              Oportunidades de ahorro
            </h3>
            <p className="text-xs text-muted-foreground">
              Cruces de datos traducidos a euros al año, ordenados por impacto.
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <SelectField
              label="Edificio"
              value={building}
              onChange={setBuilding}
              options={buildingOptions}
            />
            <ExportCsvButton
              filename={`decisiones-${range}-${building}.csv`}
              headers={[
                'Categoría',
                'Prioridad',
                'Medida',
                'Descripción',
                'Evidencia',
                'Valor',
                'Unidad',
                'Ahorro kWh/año',
                'Ahorro €/año',
              ]}
              rows={exportRows}
              disabled={!data}
            />
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            label="Ahorro potencial estimado"
            value={data ? formatEuro(data.total_savings_eur_year) : '—'}
            hint="Suma de las oportunidades accionables, por año"
            tone="success"
          />
          <StatCard
            label="Oportunidades detectadas"
            value={data ? formatNumber(data.items.length, 0) : '—'}
            hint="Priorizadas por € y evidencia"
            tone="primary"
          />
          <StatCard
            label="Medida prioritaria"
            value={data?.items[0] ? data.items[0].title : '—'}
            hint={data?.items[0] ? formatEuro(data.items[0].savings_eur_year) : undefined}
            tone="accent"
          />
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center rounded-md border border-slate-200 bg-white p-10">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}

      {error && !isLoading && (
        <div className="rounded-md border border-destructive/35 bg-white p-5">
          <p className="font-semibold text-destructive">No se pudieron cargar las oportunidades.</p>
          <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Reintentar
          </button>
        </div>
      )}

      {!isLoading && !error && data && data.items.length === 0 && (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-muted-foreground">
          No se han detectado despilfarros relevantes en el periodo seleccionado.
        </div>
      )}

      {!isLoading && !error && data && data.items.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.items.map((item) => (
            <article
              key={item.id}
              className="flex flex-col gap-3 rounded-md border border-slate-200 bg-white p-5 shadow-none"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                    {CATEGORY_LABEL[item.category]}
                  </span>
                  <h4 className="font-heading text-base font-semibold text-slate-900">
                    {item.title}
                  </h4>
                </div>
                <span
                  className={`shrink-0 rounded-sm px-2 py-0.5 text-xs font-semibold ${PRIORITY_CLASS[item.priority]}`}
                >
                  {PRIORITY_LABEL[item.priority]}
                </span>
              </div>

              <p className="text-sm text-slate-600">{item.description}</p>

              <p className="rounded-sm bg-secondary/60 px-3 py-2 text-xs text-slate-700">
                {item.evidence}
              </p>

              <div className="mt-auto flex items-end justify-between border-t border-slate-100 pt-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.08em] text-muted-foreground">
                    Ahorro estimado
                  </p>
                  <p className="font-heading text-xl font-bold text-success">
                    {formatEuro(item.savings_eur_year)}/año
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs uppercase tracking-[0.08em] text-muted-foreground">
                    Energía
                  </p>
                  <p className="text-sm font-semibold text-slate-700">
                    {formatNumber(item.savings_kwh_year, 0)} kWh/año
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
