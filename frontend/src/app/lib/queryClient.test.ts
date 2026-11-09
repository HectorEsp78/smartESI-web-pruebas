import { describe, expect, it } from 'vitest';
import { ApiError } from '../api/http';
import { shouldRetry } from './queryClient';

describe('shouldRetry', () => {
  it('does not retry client errors', () => {
    expect(shouldRetry(0, new ApiError('Periodo no válido.', 422))).toBe(false);
    expect(shouldRetry(0, new ApiError('No encontrado.', 404))).toBe(false);
  });

  it('retries server and network errors a limited number of times', () => {
    expect(shouldRetry(0, new ApiError('Error interno.', 500))).toBe(true);
    expect(shouldRetry(1, new Error('Sin conexión.'))).toBe(true);
    expect(shouldRetry(2, new Error('Sin conexión.'))).toBe(false);
  });
});
