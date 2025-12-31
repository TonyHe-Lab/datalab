import api from './api';
import type {
  DashboardSummary,
  MTBFDataPoint,
  ParetoDataPoint,
  FaultDistributionPoint,
  AnalyticsQueryParams,
} from '../types/analytics';

export const analyticsService = {
  async getSummary(params: AnalyticsQueryParams): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/api/analytics/summary', {
      params,
    });
    return response.data;
  },

  async getMTBF(params: AnalyticsQueryParams): Promise<MTBFDataPoint[]> {
    const response = await api.get<MTBFDataPoint[]>('/api/analytics/mtbf', {
      params,
    });
    return response.data;
  },

  async getPareto(params: AnalyticsQueryParams): Promise<ParetoDataPoint[]> {
    const response = await api.get<ParetoDataPoint[]>('/api/analytics/pareto', {
      params,
    });
    return response.data;
  },

  async getFaultDistribution(
    params: AnalyticsQueryParams
  ): Promise<FaultDistributionPoint[]> {
    const response = await api.get<FaultDistributionPoint[]>(
      '/api/analytics/fault-distribution',
      {
        params,
      }
    );
    return response.data;
  },
};
