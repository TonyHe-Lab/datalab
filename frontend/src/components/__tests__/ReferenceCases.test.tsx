import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReferenceCases from '../ReferenceCases';
import type { ReferenceCase } from '../../types/api';

const mockCases: ReferenceCase[] = [
  {
    id: 'WO-001',
    date: '2025-01-15',
    snippet: 'Conveyor belt malfunction at station 3',
    details: {
      work_order_id: 'WO-001',
      device_model: 'Conveyor-X1',
      fault_description: 'Conveyor belt malfunction at station 3',
      fault_code: 'ERR-001',
      component: 'Motor',
      date: '2025-01-15',
      status: 'Resolved',
    },
  },
  {
    id: 'WO-002',
    date: '2025-01-20',
    snippet: 'Sensor failure in packaging unit',
    details: {
      work_order_id: 'WO-002',
      device_model: 'Package-Pro',
      fault_description: 'Sensor failure in packaging unit',
      fault_code: 'ERR-002',
      component: 'Sensor',
      date: '2025-01-20',
      status: 'Resolved',
    },
  },
];

describe('ReferenceCases', () => {
  it('should show empty state when no cases', () => {
    render(<ReferenceCases cases={[]} loading={false} />);

    expect(screen.getByText(/enter a fault description/i)).toBeInTheDocument();
  });

  it('should show loading skeleton', () => {
    render(<ReferenceCases cases={[]} loading={true} />);

    expect(screen.getByText(/Reference Cases/i)).toBeInTheDocument();
    expect(screen.queryByText(/enter a fault description/i)).not.toBeInTheDocument();
  });

  it('should render list of cases', () => {
    render(<ReferenceCases cases={mockCases} loading={false} />);

    expect(screen.getByText('Reference Cases (2)')).toBeInTheDocument();
    expect(screen.getByText('WO-001')).toBeInTheDocument();
    expect(screen.getByText('WO-002')).toBeInTheDocument();
    expect(screen.getByText('Conveyor belt malfunction at station 3')).toBeInTheDocument();
    expect(screen.getByText('Sensor failure in packaging unit')).toBeInTheDocument();
  });

  it('should open modal when View Details is clicked', async () => {
    render(<ReferenceCases cases={mockCases} loading={false} />);

    const viewDetailsButtons = screen.getAllByText(/View Details/i);
    await userEvent.click(viewDetailsButtons[0]);

    // Modal appears, check for modal dialog
    const modal = document.querySelector('.ant-modal');
    expect(modal).toBeInTheDocument();
  });

  it('should show case ID and date tags', () => {
    render(<ReferenceCases cases={mockCases} loading={false} />);

    expect(screen.getByText('WO-001')).toBeInTheDocument();
    expect(screen.getByText('2025-01-15')).toBeInTheDocument();
    expect(screen.getByText('WO-002')).toBeInTheDocument();
    expect(screen.getByText('2025-01-20')).toBeInTheDocument();
  });
});
