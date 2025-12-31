// API response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// Diagnosis specific types
export interface DiagnosisRequest {
  query: string;
}

export interface DiagnosisResponse {
  answer: string;
  fault_code?: string;
  component?: string;
  summary?: string;
  resolution_steps?: string[];
  sources?: ReferenceCase[];
}

export interface ReferenceCase {
  id: string;
  date: string;
  snippet: string;
  details?: WorkOrderDetails;
}

export interface WorkOrderDetails {
  work_order_id: string;
  device_model: string;
  fault_description: string;
  fault_code: string;
  component: string;
  date: string;
  status: string;
  resolution?: string;
}
