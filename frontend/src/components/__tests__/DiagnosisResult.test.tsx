import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DiagnosisResult from '../DiagnosisResult';
import type { DiagnosisResponse } from '../../types/api';

describe('DiagnosisResult', () => {
  it('should show empty state when no diagnosis', () => {
    render(<DiagnosisResult diagnosis={null} />);

    expect(screen.getByText(/enter a fault description/i)).toBeInTheDocument();
  });

  it('should display diagnosis with fault code and component', () => {
    const diagnosis: DiagnosisResponse = {
      answer: 'Test answer',
      fault_code: 'ERR-001',
      component: 'Motor',
      summary: 'Test summary',
      resolution_steps: ['Step 1', 'Step 2'],
    };

    render(<DiagnosisResult diagnosis={diagnosis} />);

    expect(screen.getByText('ERR-001')).toBeInTheDocument();
    expect(screen.getByText('Motor')).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
  });

  it('should render markdown content', () => {
    const diagnosis: DiagnosisResponse = {
      answer: '# Header\n\n**Bold text** and *italic text*',
    };

    render(<DiagnosisResult diagnosis={diagnosis} />);

    expect(screen.getByText(/header/i)).toBeInTheDocument();
    expect(screen.getByText(/bold text/i)).toBeInTheDocument();
  });

  it('should display resolution steps as collapsible sections', () => {
    const diagnosis: DiagnosisResponse = {
      answer: 'Test answer',
      resolution_steps: ['Step 1: Check power', 'Step 2: Reset device'],
    };

    render(<DiagnosisResult diagnosis={diagnosis} />);

    expect(screen.getByText('Resolution Steps')).toBeInTheDocument();
    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
  });
});
