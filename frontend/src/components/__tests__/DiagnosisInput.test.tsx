import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DiagnosisInput from '../DiagnosisInput';

describe('DiagnosisInput', () => {
  it('should render text area and diagnose button', () => {
    const mockOnDiagnose = vi.fn();
    render(<DiagnosisInput onDiagnose={mockOnDiagnose} />);

    expect(screen.getByPlaceholderText(/describe the fault/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /diagnose/i })).toBeInTheDocument();
  });

  it('should disable button while loading', async () => {
    const mockOnDiagnose = vi.fn(async () => {
      await new Promise((resolve) => setTimeout(resolve, 100));
    });
    render(<DiagnosisInput onDiagnose={mockOnDiagnose} />);

    const textarea = screen.getByPlaceholderText(/describe the fault/i);
    const button = screen.getByRole('button', { name: /diagnose/i });

    fireEvent.change(textarea, {
      target: { value: 'Test fault description with enough characters' },
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(button).toHaveClass('ant-btn-loading');
    });
  });

  it('should show character count', () => {
    const mockOnDiagnose = vi.fn();
    render(<DiagnosisInput onDiagnose={mockOnDiagnose} />);

    const textarea = screen.getByPlaceholderText(/describe the fault/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Test description' } });

    expect(screen.getByText(/16 \/ 500/)).toBeInTheDocument();
  });

  it('should show validation error for short input', async () => {
    const mockOnDiagnose = vi.fn();
    render(<DiagnosisInput onDiagnose={mockOnDiagnose} />);

    const button = screen.getByRole('button', { name: /diagnose/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/please enter a fault description/i)).toBeInTheDocument();
    });
  });

  it('should clear form on Clear button click', async () => {
    const mockOnDiagnose = vi.fn();
    render(<DiagnosisInput onDiagnose={mockOnDiagnose} />);

    const textarea = screen.getByPlaceholderText(/describe the fault/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Test description' } });

    const clearButton = screen.getByRole('button', { name: /clear/i });
    await userEvent.click(clearButton);

    expect(screen.getByText(/0 \/ 500/)).toBeInTheDocument();
  });
});
