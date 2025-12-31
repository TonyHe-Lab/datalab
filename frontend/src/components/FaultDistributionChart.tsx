import { Card } from 'antd';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import type { FaultDistributionPoint } from '../types/analytics';

interface FaultDistributionChartProps {
  data?: FaultDistributionPoint[];
  loading?: boolean;
}

export default function FaultDistributionChart({
  data = [],
  loading = false,
}: FaultDistributionChartProps) {
  if (loading) {
    return <Card title="Fault Distribution" loading={loading} />;
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Fault Distribution">
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#8c8c8c' }}>No data available</span>
        </div>
      </Card>
    );
  }

  const COLORS = [
    '#1890ff',
    '#52c41a',
    '#faad14',
    '#f5222d',
    '#722ed1',
    '#eb2f96',
    '#13c2c2',
    '#fa8c16',
  ];

  return (
    <Card title="Fault Distribution">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="fault_code"
            cx="50%"
            cy="50%"
            label
            outerRadius={80}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${entry.fault_code}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined) => [
              value ?? 0,
              'Count',
            ]}
            labelFormatter={(value) => `Fault Code: ${value}`}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
}
