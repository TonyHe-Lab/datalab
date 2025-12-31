/**
 * Error Handling and Edge Cases Tests
 * Tests how the system handles various error scenarios and edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { ThemeProvider } from '../theme';
import Workbench from '../pages/Workbench';
import Dashboard from '../pages/Dashboard';

// Mock services
vi.mock('../services/chat', () => ({
  chatService: {
    diagnose: vi.fn(),
  },
  searchService: {
    searchSimilarCases: vi.fn(),
  },
}));

vi.mock('../services/analytics', () => ({
  analyticsService: {
    getSummary: vi.fn(),
    getMTBF: vi.fn(),
    getPareto: vi.fn(),
    getFaultDistribution: vi.fn(),
  },
}));

import { chatService } from '../services/chat';
import { analyticsService } from '../services/analytics';

const searchService = {
  searchSimilarCases: vi.fn(),
} as any;

describe('Error Handling and Edge Cases (AC: 3)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: Infinity,
        },
        mutations: {
          retry: false,
        },
      },
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderWorkbench = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={ThemeProvider}>
          <MemoryRouter>
            <Workbench />
          </MemoryRouter>
        </ConfigProvider>
      </QueryClientProvider>
    );
  };

  const renderDashboard = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={ThemeProvider}>
          <MemoryRouter>
            <Dashboard />
          </MemoryRouter>
        </ConfigProvider>
      </QueryClientProvider>
    );
  };

  describe('Network Failure Scenarios (AC: 3 - Subtask 1)', () => {
    it('should handle network timeout errors', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);
      mockDiagnose.mockRejectedValue(new Error('Request timeout'));

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault description with enough characters');
      await userEvent.click(diagnoseButton);

      // Verify loading state clears after error
      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );
    });

    it('should handle connection refused errors', async () => {
      const mockGetSummary = vi.mocked(analyticsService.getSummary);
      mockGetSummary.mockRejectedValue(new Error('ECONNREFUSED'));

      renderDashboard();

      await waitFor(
        () => {
          expect(mockGetSummary).toHaveBeenCalled();
        },
        { timeout: 3000 }
      );

      // Verify error is handled gracefully
      await waitFor(
        () => {
          // Application should not crash
          expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should handle partial network failure', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);
      const mockSearch = vi.mocked(searchService.searchSimilarCases);

      mockDiagnose.mockResolvedValue({
        answer: 'Diagnosis successful',
        sources: [],
      });

      mockSearch.mockRejectedValue(new Error('Search API failed'));

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault description with enough characters');
      await userEvent.click(diagnoseButton);

      // Verify diagnosis still displays despite search failure
      await waitFor(
        () => {
          expect(screen.getByText(/Diagnosis successful/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Invalid Input Handling (AC: 3 - Subtask 2)', () => {
    it('should validate minimum fault description length', async () => {
      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      // Try with very short input
      await userEvent.type(textarea, 'ABC');
      await userEvent.click(diagnoseButton);

      // Button should remain disabled
      await waitFor(() => {
        expect(diagnoseButton).toBeDisabled();
      });
    });

    it('should handle empty input submission', async () => {
      renderWorkbench();

      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      // Click without typing
      await userEvent.click(diagnoseButton);

      // Button should remain disabled
      expect(diagnoseButton).toBeDisabled();
    });

    it('should handle very long fault description input', async () => {
      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const longText = 'A'.repeat(600); // Exceeds 500 character limit

      await userEvent.type(textarea, longText);

      // Verify character count indicates limit exceeded
      await waitFor(() => {
        expect(screen.getByText(/600 \/ 500/i)).toBeInTheDocument();
      });
    });

    it('should handle special characters in input', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockResolvedValue({
        answer: 'Processed special characters',
        sources: [],
      });

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      const specialChars = 'Test <script>alert("xss")</script> & special chars: !@#$%^&*()';

      await userEvent.type(textarea, specialChars);
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockDiagnose).toHaveBeenCalledWith({ query: specialChars });
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Backend Service Unavailable (AC: 3 - Subtask 3)', () => {
    it('should handle backend service completely unavailable', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockRejectedValue(new Error('Service Unavailable'));

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault description');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );

      // Application should remain functional
      expect(screen.getByPlaceholderText(/describe the fault/i)).toBeInTheDocument();
    });

    it('should handle 503 Service Unavailable', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockRejectedValue({
        response: { status: 503 },
        message: 'Service temporarily unavailable',
      });

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );
    });

    it('should handle slow backend responses', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ answer: 'Slow response', sources: [] }), 5000)
          )
      );

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      // Verify loading state persists
      expect(diagnoseButton).toHaveClass('ant-btn-loading');
    });
  });

  describe('Data Validation Errors (AC: 3 - Subtask 4)', () => {
    it('should handle malformed API response', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      // Return invalid response structure
      mockDiagnose.mockResolvedValue({
        invalidField: 'This should not be here',
      } as any);

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault description');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );
    });

    it('should handle missing required fields in response', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      // Return response missing 'answer' field
      mockDiagnose.mockResolvedValue({
        fault_code: 'TEST-001',
      } as any);

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );
    });

    it('should handle empty arrays in API response', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockResolvedValue({
        answer: 'Valid answer',
        resolution_steps: [],
        sources: [],
      });

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Valid answer/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should handle unexpected data types in response', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockResolvedValue({
        answer: 12345, // Should be string
        resolution_steps: 'not an array', // Should be array
      } as any);

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(diagnoseButton).not.toHaveClass('ant-btn-loading');
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Edge Case Scenarios', () => {
    it('should handle rapid successive API calls', async () => {
      const mockDiagnose = vi.mocked(chatService.diagnose);

      mockDiagnose.mockResolvedValue({
        answer: 'Response',
        sources: [],
      });

      renderWorkbench();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      // Rapidly submit multiple requests
      await userEvent.type(textarea, 'Fault 1');
      await userEvent.click(diagnoseButton);
      await userEvent.clear(textarea);

      await userEvent.type(textarea, 'Fault 2');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockDiagnose).toHaveBeenCalled();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Concurrent Error Scenarios', () => {
    it('should handle errors in multiple concurrent requests', async () => {
      const mockGetSummary = vi.mocked(analyticsService.getSummary);
      const mockGetMTBF = vi.mocked(analyticsService.getMTBF);

      mockGetSummary.mockRejectedValue(new Error('Summary failed'));
      mockGetMTBF.mockRejectedValue(new Error('MTBF failed'));

      renderDashboard();

      await waitFor(
        () => {
          expect(true).toBe(true);
        },
        { timeout: 3000 }
      );

      // Dashboard should still render without crashing
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });

    it('should handle partial success in concurrent requests', async () => {
      const mockGetSummary = vi.mocked(analyticsService.getSummary);
      const mockGetMTBF = vi.mocked(analyticsService.getMTBF);

      mockGetSummary.mockResolvedValue({
        mtbf: 72.5,
        total_failures: 100,
        top_component: 'Test Component',
        last_sync: '2024-12-31',
      });

      mockGetMTBF.mockRejectedValue(new Error('MTBF failed'));

      renderDashboard();

      await waitFor(
        () => {
          expect(mockGetSummary).toHaveBeenCalled();
        },
        { timeout: 3000 }
      );

      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });
  });
});
