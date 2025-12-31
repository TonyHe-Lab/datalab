// Analytics data types

export interface DashboardSummary {
  mtbf: number;
  total_failures: number;
  top_component: string;
  last_sync: string;
}

export interface MTBFDataPoint {
  date: string;
  mtbf: number;
  equipment_id?: string;
}

export interface ParetoDataPoint {
  component: string;
  count: number;
  percentage: number;
}

export interface FaultDistributionPoint {
  fault_code: string;
  count: number;
  [key: string]: number | string;
}

export interface AnalyticsFilters {
  startDate: string;
  endDate: string;
  equipmentModel?: string;
}

export interface AnalyticsQueryParams {
  start_date: string;
  end_date: string;
  equipment_model?: string;
}
