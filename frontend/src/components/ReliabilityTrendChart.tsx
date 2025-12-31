import { Card } from 'antd';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { MTBFDataPoint } from '../types/analytics';

interface ReliabilityTrendChartProps {
  data?: MTBFDataPoint[];
  loading?: boolean;
}

export default function ReliabilityTrendChart({
  data = [],
  loading = false,
}: ReliabilityTrendChartProps) {
  if (loading) {
    return (
      <Card title="Reliability Trend (MTBF)" loading={loading} />
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Reliability Trend (MTBF)">
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#8c8c8c' }}>No data available</span>
        </div>
      </Card>
    );
  }

  return (
    <Card title="Reliability Trend (MTBF)">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }}
          />
          <YAxis label={{ value: 'MTBF (hrs)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            labelFormatter={(value) => {
              const date = new Date(value as string);
              return date.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'long',
                day: 'numeric',
              });
            }}
            formatter={(value: number | undefined) => [
              typeof value === 'number' ? value.toFixed(1) : '-',
              'MTBF (hrs)',
            ]}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="mtbf"
            stroke="#1890ff"
            strokeWidth={2}
            dot={{ fill: '#1890ff', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
