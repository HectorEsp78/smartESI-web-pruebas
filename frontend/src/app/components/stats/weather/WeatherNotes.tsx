interface WeatherNotesProps {
  notes: string[];
}

export function WeatherNotes({ notes }: WeatherNotesProps) {
  if (notes.length === 0) return null;
  return (
    <details className="rounded-md border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600">
      <summary className="cursor-pointer font-semibold text-slate-700">
        Criterios y limitaciones de los datos
      </summary>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        {notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </details>
  );
}
