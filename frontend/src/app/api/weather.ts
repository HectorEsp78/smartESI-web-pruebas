import { buildQuery, getJson } from './http';
import type { WeatherOverviewDto } from '../types/weather';

export function fetchWeatherOverview(
  days: number,
  signal?: AbortSignal,
): Promise<WeatherOverviewDto> {
  const query = buildQuery({ days: String(days) });
  return getJson<WeatherOverviewDto>(`/api/v1/weather/overview?${query}`, signal);
}
