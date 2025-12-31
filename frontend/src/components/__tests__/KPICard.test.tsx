import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KPICard, DashboardKPI } from '../KPICard';
import type { DashboardSummary } from '../../types/analytics';

describe('KPICard', () => {
  it('should render title and value', () => {
    render(<KPICard title="Test Metric" value={123.45} icon={<span>📊</span>} />);

    expect(screen.getByText('Test Metric')).toBeInTheDocument();
    expect(screen.getByText('123')).toBeInTheDocument();
  });

  it('should render with suffix', () => {
    render(
      <KPICard
        title="Value"
        value={100}
        suffix="hrs"
        icon={<span>⚡</span>}
      />
    );

    expect(screen.getByText('hrs')).toBeInTheDocument();
  });

  it('should show loading skeleton', () => {
    render(
      <KPICard title="Loading" value={0} loading icon={<span>📊</span>} />
    );

    const skeleton = document.querySelector('.ant-skeleton');
    expect(skeleton).toBeInTheDocument();
  });
});

describe('DashboardKPI', () => {
  it('should render all four KPI cards with data', () => {
    const summary: DashboardSummary = {
      mtbf: 123.4,
      total_failures: 45,
      top_component: 'Motor-X1',
      last_sync: '2025-12-31T12:00:00Z',
    };

    render(<DashboardKPI summary={summary} />);

    expect(screen.getByText('MTBF')).toBeInTheDocument();
    const kpiText = document.body.textContent ?? '';
    expect(kpiText).toContain('123');
    expect(screen.getByText('Total Failures')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('Top Component')).toBeInTheDocument();
    expect(screen.getByText('Last Sync')).toBeInTheDocument();
  });

  it('should render loading placeholders when loading', () => {
    render(<DashboardKPI loading />);

    const skeletons = document.querySelectorAll('.ant-skeleton');
    expect(skeletons.length).toBe(4);
  });

  it('should render empty state without summary', () => {
    render(<DashboardKPI />);

    expect(screen.getByText('MTBF')).toBeInTheDocument();
  });
});
