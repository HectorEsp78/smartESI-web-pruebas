export type DecisionRange = 'day' | 'week' | 'month' | 'year';

export type OpportunityCategory =
  | 'iluminacion'
  | 'calefaccion'
  | 'electricidad'
  | 'tendencia';

export type OpportunityPriority = 'alta' | 'media' | 'baja';

export interface OpportunityDto {
  id: string;
  category: OpportunityCategory;
  title: string;
  description: string;
  evidence: string;
  metric_value: number;
  metric_unit: string;
  savings_kwh_year: number;
  savings_eur_year: number;
  priority: OpportunityPriority;
}

export interface DecisionsDto {
  range: DecisionRange;
  building_id: string;
  total_savings_eur_year: number;
  items: OpportunityDto[];
}
