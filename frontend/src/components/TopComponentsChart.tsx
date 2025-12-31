import { Card } from 'antd';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ParetoDataPoint } from '../types/analytics';

interface TopComponentsChartProps {
  data?: ParetoDataPoint[];
  loading?: boolean;
}

export default function TopComponentsChart({
  data = [],
  loading = false,
}: TopComponentsChartProps) {
  if (loading) {
    return <Card title="Top Failing Components" loading={loading} />;
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Top Failing Components">
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#8c8c8c' }}>No data available</span>
        </div>
      </Card>
    );
  }

  const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];

  return (
    <Card title="Top Failing Components">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="component" type="category" width={90} />
          <Tooltip
            formatter={(value: number | undefined) => [
              value ?? 0,
              'Count',
            ]}
            labelFormatter={(value) => `Component: ${value}`}
          />
          <Legend />
          <Bar dataKey="count" name="Failure Count">
            {data.map((entry, index) => (
              <Cell
                key={`cell-${entry.component}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
