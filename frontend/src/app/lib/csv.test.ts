import { describe, expect, it } from 'vitest';
import { toCsv } from './csv';

describe('toCsv', () => {
  it('writes a header and one row per record', () => {
    const csv = toCsv(
      ['Espacio', 'kWh'],
      [
        ['A11', 12.5],
        ['A12', 8],
      ],
    );

    expect(csv).toBe('Espacio;kWh\r\nA11;12.5\r\nA12;8\r\n');
  });

  it('quotes values containing the delimiter, quotes or line breaks', () => {
    const csv = toCsv(['Texto'], [['Aula; grande'], ['Dice "hola"'], ['dos\nlíneas']]);

    expect(csv).toContain('"Aula; grande"');
    expect(csv).toContain('"Dice ""hola"""');
    expect(csv).toContain('"dos\nlíneas"');
  });

  it('supports another delimiter', () => {
    expect(toCsv(['a', 'b'], [[1, 2]], ',')).toBe('a,b\r\n1,2\r\n');
  });

  it('keeps empty values as empty cells', () => {
    expect(toCsv(['a', 'b'], [[null, undefined]])).toBe('a;b\r\n;\r\n');
  });
});
