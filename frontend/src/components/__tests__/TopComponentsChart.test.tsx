import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TopComponentsChart from '../TopComponentsChart';
import type { ParetoDataPoint } from '../../types/analytics';

vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('TopComponentsChart', () => {
  const mockData: ParetoDataPoint[] = [
    { component: 'Motor', count: 45, percentage: 35 },
    { component: 'Sensor', count: 30, percentage: 23 },
    { component: 'Belt', count: 25, percentage: 19 },
  ];

  it('should render chart with data', () => {
    render(<TopComponentsChart data={mockData} />);

    expect(screen.getByText('Top Failing Components')).toBeInTheDocument();
  });

  it('should display loading skeleton', () => {
    render(<TopComponentsChart loading />);

    const skeleton = document.querySelector('.ant-skeleton');
    expect(skeleton).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    render(<TopComponentsChart data={[]} />);

    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });
});
