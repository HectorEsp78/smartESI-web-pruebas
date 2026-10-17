import type { ChangeEvent } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
}

export function SelectField({ label, value, onChange, options }: SelectFieldProps) {
  return (
    <label className="inline-flex items-center gap-2 text-xs text-slate-600">
      <span className="font-semibold uppercase tracking-[0.08em]">{label}</span>
      <select
        value={value}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value)}
        className="cursor-pointer rounded-sm border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/40"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
