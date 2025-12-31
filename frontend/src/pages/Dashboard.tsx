import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Typography, Row, Col } from 'antd';
import type { AnalyticsFilters, AnalyticsQueryParams } from '../types/analytics';
import { analyticsService } from '../services/analytics';
import { DashboardKPI } from '../components/KPICard';
import ReliabilityTrendChart from '../components/ReliabilityTrendChart';
import TopComponentsChart from '../components/TopComponentsChart';
import FaultDistributionChart from '../components/FaultDistributionChart';
import DashboardFilters from '../components/DashboardFilters';

const { Title } = Typography;

export default function DashboardPage() {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    startDate: '2025-12-01',
    endDate: '2025-12-31',
    equipmentModel: undefined,
  });

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary', filters],
    queryFn: () => {
      const queryParams: AnalyticsQueryParams = {
        start_date: filters.startDate,
        end_date: filters.endDate,
        equipment_model: filters.equipmentModel,
      };
      return analyticsService.getSummary(queryParams);
    },
  });

  const { data: mtbfData, isLoading: mtbfLoading } = useQuery({
    queryKey: ['analytics-mtbf', filters],
    queryFn: () => {
      const queryParams: AnalyticsQueryParams = {
        start_date: filters.startDate,
        end_date: filters.endDate,
        equipment_model: filters.equipmentModel,
      };
      return analyticsService.getMTBF(queryParams);
    },
  });

  const { data: paretoData, isLoading: paretoLoading } = useQuery({
    queryKey: ['analytics-pareto', filters],
    queryFn: () => {
      const queryParams: AnalyticsQueryParams = {
        start_date: filters.startDate,
        end_date: filters.endDate,
        equipment_model: filters.equipmentModel,
      };
      return analyticsService.getPareto(queryParams);
    },
  });

  const { data: faultDistribution, isLoading:_faultDistributionLoading } =
    useQuery({
      queryKey: ['analytics-fault-distribution', filters],
      queryFn: () => {
        const queryParams: AnalyticsQueryParams = {
          start_date: filters.startDate,
          end_date: filters.endDate,
          equipment_model: filters.equipmentModel,
        };
        return analyticsService.getFaultDistribution(queryParams);
      },
    });

  const handleFilterChange = (newFilters: AnalyticsFilters) => {
    setFilters(newFilters);
  };

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f0f2f5' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>
        Analytics Dashboard
      </Title>

      <DashboardFilters
        onFilterChange={handleFilterChange}
        loading={summaryLoading}
      />

      <div style={{ marginBottom: '24px' }}>
        <DashboardKPI
          summary={summary}
          loading={summaryLoading}
        />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <ReliabilityTrendChart
            data={mtbfData}
            loading={mtbfLoading}
          />
        </Col>

        <Col xs={24} lg={12}>
          <TopComponentsChart
            data={paretoData}
            loading={paretoLoading}
          />
        </Col>

        <Col xs={24}>
          <FaultDistributionChart
            data={faultDistribution}
            loading={_faultDistributionLoading}
          />
        </Col>
      </Row>
    </div>
  );
}
