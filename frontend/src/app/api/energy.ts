import { buildQuery, getJson } from './http';
import type {
  EnergyBreakdownDto,
  EnergyByBuildingDto,
  EnergyCompareDto,
  EnergyConsumptionDto,
  EnergyEfficiencyDto,
  EnergyMetric,
  EnergyRange,
} from '../types/energy';

export function fetchEnergyConsumption(
  range: EnergyRange,
  building: string,
  metric: EnergyMetric,
  signal?: AbortSignal,
): Promise<EnergyConsumptionDto> {
  const query = buildQuery({ range, building, metric });
  return getJson<EnergyConsumptionDto>(`/api/v1/energy/consumption?${query}`, signal);
}

export function fetchEnergyByBuilding(
  range: EnergyRange,
  metric: EnergyMetric,
  signal?: AbortSignal,
): Promise<EnergyByBuildingDto> {
  const query = buildQuery({ range, metric });
  return getJson<EnergyByBuildingDto>(`/api/v1/energy/by-building?${query}`, signal);
}

export function fetchEnergyBreakdown(
  range: EnergyRange,
  building: string,
  signal?: AbortSignal,
): Promise<EnergyBreakdownDto> {
  const query = buildQuery({ range, building });
  return getJson<EnergyBreakdownDto>(`/api/v1/energy/breakdown?${query}`, signal);
}

export function fetchEnergyCompare(
  range: EnergyRange,
  building: string,
  metric: EnergyMetric,
  signal?: AbortSignal,
): Promise<EnergyCompareDto> {
  const query = buildQuery({ range, building, metric });
  return getJson<EnergyCompareDto>(`/api/v1/energy/compare?${query}`, signal);
}

export function fetchEnergyEfficiency(
  range: EnergyRange,
  signal?: AbortSignal,
): Promise<EnergyEfficiencyDto> {
  const query = buildQuery({ range });
  return getJson<EnergyEfficiencyDto>(`/api/v1/energy/efficiency?${query}`, signal);
}
