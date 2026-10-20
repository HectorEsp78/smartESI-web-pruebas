import { downloadCsv } from '../../lib/csv';
import type { CsvValue } from '../../lib/csv';

interface ExportCsvButtonProps {
  filename: string;
  headers: string[];
  rows: CsvValue[][];
  disabled?: boolean;
}

export function ExportCsvButton({
  filename,
  headers,
  rows,
  disabled = false,
}: ExportCsvButtonProps) {
  return (
    <button
      type="button"
      onClick={() => downloadCsv(filename, headers, rows)}
      disabled={disabled || rows.length === 0}
      className="cursor-pointer rounded-sm border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
    >
      Exportar CSV
    </button>
  );
}
