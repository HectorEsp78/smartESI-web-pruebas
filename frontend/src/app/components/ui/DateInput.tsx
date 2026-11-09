interface DateInputProps {
  label: string;
  value: string;
  min?: string;
  max?: string;
  onChange: (value: string) => void;
}

export function DateInput({ label, value, min, max, onChange }: DateInputProps) {
  return (
    <label className="inline-flex flex-col gap-1 text-xs text-slate-600">
      <span className="font-semibold uppercase tracking-[0.08em]">{label}</span>
      <input
        type="date"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-sm border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
      />
    </label>
  );
}
