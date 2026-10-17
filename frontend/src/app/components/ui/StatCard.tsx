interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: 'primary' | 'accent' | 'success' | 'warning' | 'neutral';
}

const TONE_CLASS: Record<NonNullable<StatCardProps['tone']>, string> = {
  primary: 'text-primary',
  accent: 'text-accent',
  success: 'text-success',
  warning: 'text-warning',
  neutral: 'text-slate-900',
};

export function StatCard({ label, value, hint, tone = 'neutral' }: StatCardProps) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-none">
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {label}
      </p>
      <p className={`mt-2 font-heading text-2xl font-bold ${TONE_CLASS[tone]}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
