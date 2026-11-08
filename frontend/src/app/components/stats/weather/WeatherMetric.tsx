interface WeatherMetricProps {
  label: string;
  value: string;
  hint?: string;
  tone?: 'primary' | 'accent' | 'success' | 'warning' | 'neutral';
}

const TONE_CLASS: Record<NonNullable<WeatherMetricProps['tone']>, string> = {
  primary: 'text-primary',
  accent: 'text-accent',
  success: 'text-success',
  warning: 'text-warning',
  neutral: 'text-slate-900',
};

export function WeatherMetric({
  label,
  value,
  hint,
  tone = 'neutral',
}: WeatherMetricProps) {
  return (
    <div className="rounded-sm border border-slate-100 bg-slate-50/70 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">
        {label}
      </p>
      <p className={`mt-1 font-heading text-lg font-bold ${TONE_CLASS[tone]}`}>
        {value}
      </p>
      {hint && <p className="mt-0.5 text-[11px] text-slate-500">{hint}</p>}
    </div>
  );
}
