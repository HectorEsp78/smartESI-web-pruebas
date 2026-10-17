export interface BuildingRefDto {
  id: string;
  label: string;
  max_capacity: number;
  area_m2: number;
  lighting_kw: number;
  setpoint_c: number;
}

export interface SpaceRefDto {
  id: string;
  label: string;
  building_id: string;
  kind: string;
  area_m2: number;
  lighting_kw: number;
  has_valve: boolean;
}

export interface MetaDto {
  buildings: BuildingRefDto[];
  spaces: SpaceRefDto[];
}
