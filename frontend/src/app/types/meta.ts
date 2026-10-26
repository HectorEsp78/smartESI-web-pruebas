export interface BuildingRefDto {
  id: string;
  label: string;
}

export interface MetaDto {
  buildings: BuildingRefDto[];
}
