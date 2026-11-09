/** Shown instead of a blank page when a component fails while rendering. */
export function RouteError() {
  return (
    <div className="app-shell flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-heading text-3xl font-extrabold uppercase tracking-[0.08em] text-accent">
        Algo ha fallado
      </h1>
      <p className="text-slate-600">No se pudo mostrar esta página. Prueba a recargarla.</p>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="cursor-pointer rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Recargar
      </button>
    </div>
  );
}
