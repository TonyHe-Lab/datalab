import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import FaultDistributionChart from '../FaultDistributionChart';
import type { FaultDistributionPoint } from '../../types/analytics';

vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('FaultDistributionChart', () => {
  const mockData: FaultDistributionPoint[] = [
    { fault_code: 'ERR-001', count: 45 },
    { fault_code: 'ERR-002', count: 30 },
    { fault_code: 'ERR-003', count: 25 },
  ];

  it('should render chart with data', () => {
    render(<FaultDistributionChart data={mockData} />);

    expect(screen.getByText('Fault Distribution')).toBeInTheDocument();
  });

  it('should display loading skeleton', () => {
    render(<FaultDistributionChart loading />);

    const skeleton = document.querySelector('.ant-skeleton');
    expect(skeleton).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    render(<FaultDistributionChart data={[]} />);

    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });
});
