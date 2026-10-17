import { Link } from 'react-router';

export function NotFound() {
  return (
    <div className="app-shell flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-heading text-3xl font-extrabold uppercase tracking-[0.08em] text-accent">
        404
      </h1>
      <p className="text-slate-600">La página que buscas no existe.</p>
      <Link
        to="/"
        className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Volver al panel
      </Link>
    </div>
  );
}
