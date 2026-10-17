import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  subtitle: string;
  unit?: string;
  headerExtra?: ReactNode;
  isLoading: boolean;
  error: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry: () => void;
  height?: number;
  children: ReactNode;
}

export function ChartCard({
  title,
  subtitle,
  unit,
  headerExtra,
  isLoading,
  error,
  isEmpty = false,
  emptyMessage = 'Sin datos para el periodo seleccionado.',
  onRetry,
  height = 300,
  children,
}: ChartCardProps) {
  const header = (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
      <div>
        <h3 className="font-heading text-lg font-semibold text-slate-900">{title}</h3>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2">
        {headerExtra}
        {unit && (
          <span className="shrink-0 rounded-sm border border-slate-200 bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
            {unit}
          </span>
        )}
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
        {header}
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/35 bg-white p-5 shadow-none">
        {header}
        <p className="font-semibold text-destructive">No se pudieron cargar los datos.</p>
        <p className="mt-1 text-sm text-destructive/90">{error.message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 bg-white p-5 shadow-none">
        {header}
        <div
          className="flex flex-col items-center justify-center gap-3 text-center"
          style={{ height }}
        >
          <svg viewBox="0 0 120 24" className="h-6 w-full text-slate-400" aria-hidden="true">
            <line
              x1="4"
              y1="12"
              x2="116"
              y2="12"
              stroke="currentColor"
              strokeWidth="2"
              strokeDasharray="6 6"
            />
          </svg>
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-slate-200 bg-white p-5 shadow-none">
      {header}
      <div style={{ height }}>{children}</div>
    </div>
  );
}
