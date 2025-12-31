import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReliabilityTrendChart from '../ReliabilityTrendChart';
import type { MTBFDataPoint } from '../../types/analytics';

// Mock Recharts to avoid rendering issues in tests
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('ReliabilityTrendChart', () => {
  const mockData: MTBFDataPoint[] = [
    { date: '2025-12-01', mtbf: 120.5 },
    { date: '2025-12-02', mtbf: 130.2 },
    { date: '2025-12-03', mtbf: 125.8 },
  ];

  it('should render chart with data', () => {
    render(<ReliabilityTrendChart data={mockData} />);

    expect(screen.getByText('Reliability Trend (MTBF)')).toBeInTheDocument();
  });

  it('should display loading skeleton', () => {
    render(<ReliabilityTrendChart loading />);

    const skeleton = document.querySelector('.ant-skeleton');
    expect(skeleton).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    render(<ReliabilityTrendChart data={[]} />);

    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });
});
