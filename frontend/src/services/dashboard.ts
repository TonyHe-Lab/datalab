import api from './api';

export interface ActivityItem {
  id: string
  type: string
  timestamp: string
  description: string
}

export interface DashboardStats {
  totalWorkOrders: number
  averageResponseTime: number
  piiScrubbedCount: number
  recentActivity: ActivityItem[]
}

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/dashboard');
    return response.data;
  },
};
