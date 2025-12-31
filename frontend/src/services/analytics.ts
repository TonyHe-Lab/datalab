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
    const response = await api.get<{success: boolean, data: DashboardSummary}>('/analytics/summary', {
      params,
    });
    return response.data.data;
  },

  async getMTBF(params: AnalyticsQueryParams): Promise<MTBFDataPoint[]> {
    const response = await api.get<{success: boolean, data: MTBFDataPoint[]}>('/analytics/mtbf', {
      params,
    });
    return response.data.data;
  },

  async getPareto(params: AnalyticsQueryParams): Promise<ParetoDataPoint[]> {
    const response = await api.get<{success: boolean, data: ParetoDataPoint[]}>('/analytics/pareto', {
      params,
    });
    return response.data.data;
  },

  async getFaultDistribution(
    params: AnalyticsQueryParams
  ): Promise<FaultDistributionPoint[]> {
    const response = await api.get<{success: boolean, data: FaultDistributionPoint[]}>(
      '/analytics/fault-distribution',
      {
        params,
      }
    );
    return response.data.data;
  },
};
