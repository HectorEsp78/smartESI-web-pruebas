import { buildQuery, getJson } from './http';
import type { WeatherOverviewDto } from '../types/weather';

export interface WeatherPeriod {
  start: string;
  end: string;
}

export function fetchWeatherOverview(
  period: WeatherPeriod,
  signal?: AbortSignal,
): Promise<WeatherOverviewDto> {
  const query = buildQuery({ start: period.start, end: period.end });
  return getJson<WeatherOverviewDto>(`/api/v1/weather/overview?${query}`, signal);
}
