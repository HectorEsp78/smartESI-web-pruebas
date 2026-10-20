export type CsvValue = string | number | boolean | null | undefined;

function escapeCell(value: CsvValue, delimiter: string): string {
  if (value === null || value === undefined) return '';
  const text = String(value);
  // Quote when the value contains the separator, quotes or a line break.
  const needsQuotes = text.includes(delimiter) || /["\n\r]/.test(text);
  if (needsQuotes) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

/** Build a CSV document (semicolon-separated by default: Excel-friendly in es-ES). */
export function toCsv(
  headers: string[],
  rows: CsvValue[][],
  delimiter = ';',
): string {
  const lines = [headers, ...rows].map((row) =>
    row.map((value) => escapeCell(value, delimiter)).join(delimiter),
  );
  return `${lines.join('\r\n')}\r\n`;
}

/** Trigger a browser download of the given rows. */
export function downloadCsv(
  filename: string,
  headers: string[],
  rows: CsvValue[][],
  delimiter = ';',
): void {
  const csv = toCsv(headers, rows, delimiter);
  // The BOM makes Excel detect UTF-8 (accents, €, ₂).
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
