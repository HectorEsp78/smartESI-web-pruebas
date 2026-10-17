interface Option<T extends string> {
  value: T;
  label: string;
}

interface RangeSelectorProps<T extends string> {
  options: ReadonlyArray<Option<T>>;
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
}

export function RangeSelector<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: RangeSelectorProps<T>) {
  return (
    <div className="inline-flex flex-wrap gap-2" role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            aria-pressed={isActive}
            className={`cursor-pointer rounded-sm border px-3 py-1.5 text-xs transition-colors ${
              isActive
                ? 'border-primary bg-primary font-semibold text-primary-foreground'
                : 'border-slate-300 bg-white text-slate-700 hover:border-primary hover:text-primary'
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
