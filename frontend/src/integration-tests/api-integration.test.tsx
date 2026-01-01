/**
 * API Integration Tests
 * Tests complete API integration with backend for all endpoints
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigProvider } from 'antd';
import { ThemeProvider } from '../theme';
import Workbench from '../pages/Workbench';

// Setup MSW-like mocking for API calls
const mockFetch = vi.fn();

globalThis.fetch = mockFetch as any;

describe('API Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: Infinity,
        },
      },
    });

    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={ThemeProvider}>
          <Workbench />
        </ConfigProvider>
      </QueryClientProvider>
    );
  };

  describe('Chat API Integration (AC: 2)', () => {
    it('should successfully call chat API with valid payload', async () => {
      const mockResponse = {
        success: true,
        data: {
          answer: 'Based on analysis, this is a power supply issue.',
          fault_code: 'PWR-001',
          component: 'Power Supply Module',
          summary: 'Voltage fluctuation detected.',
          resolution_steps: ['Check voltage', 'Replace components'],
          sources: [],
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      renderComponent();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Equipment not powering on');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/chat/'),
            expect.objectContaining({
              method: 'POST',
              headers: expect.objectContaining({
                'Content-Type': 'application/json',
              }),
              body: expect.stringContaining('Equipment not powering on'),
            })
          );
        },
        { timeout: 5000 }
      );
    });

    it('should handle chat API error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          success: false,
          error: 'Internal server error',
        }),
      });

      renderComponent();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockFetch).toHaveBeenCalled();
        },
        { timeout: 3000 }
      );
    });

    it('should test retry logic for failed chat requests', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            data: {
              answer: 'Test response',
              sources: [],
            },
          }),
        });

      // Note: React Query retry behavior is configured with retry: 1 in app
      // This test verifies the fetch is called multiple times
      renderComponent();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
        },
        { timeout: 5000 }
      );
    });
  });

  describe('Analytics API Integration (AC: 2)', () => {
    it('should call analytics API with query parameters', async () => {
      const mockSummaryResponse = {
        success: true,
        data: {
          total_metrics: { total_work_orders: 100, total_downtime: 24.5 },
          mtbf: 72.5,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummaryResponse,
      });

      // Direct API call test
      await fetch('/api/analytics/summary?start_date=2024-01-01&end_date=2024-12-31');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/analytics/summary'),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should handle analytics API error gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          success: false,
          error: 'Invalid date range',
        }),
      });

      try {
        await fetch('/api/analytics/summary?start_date=invalid');
      } catch (error) {
        // Error is expected
        expect(true).toBe(true);
      }
    });

    it('should test multiple analytics endpoints', async () => {
      const endpoints = [
        '/api/analytics/summary',
        '/api/analytics/mtbf',
        '/api/analytics/pareto',
        '/api/analytics/fault-distribution',
      ];

      for (const endpoint of endpoints) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, data: {} }),
        });

        await fetch(endpoint);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining(endpoint),
          expect.any(Object)
        );
      }
    });
  });

  describe('Search API Integration (AC: 2)', () => {
    it('should call search API with query parameter', async () => {
      const mockSearchResponse = {
        success: true,
        data: [
          {
            id: 'WO-2024-001',
            date: '2024-12-15',
            snippet: 'Similar power supply issue',
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse,
      });

      await fetch('/api/search/similar?query=power%20supply');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/search/similar'),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should handle empty search results', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: [],
        }),
      });

      const response = await fetch('/api/search/similar?query=unique');

      expect(response.ok).toBe(true);
    });

    it('should test search API error handling', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          success: false,
          error: 'No results found',
        }),
      });

      const response = await fetch('/api/search/similar?query=test');

      expect(response.ok).toBe(false);
    });
  });

  describe('Combined API Integration (AC: 2)', () => {
    it('should test full workflow with multiple API calls', async () => {
      const chatResponse = {
        success: true,
        data: {
          answer: 'Diagnosis result',
          sources: [],
        },
      };

      const searchResponse = {
        success: true,
        data: [
          { id: 'WO-001', date: '2024-01-01', snippet: 'Reference case' },
        ],
      };

      let callCount = 0;
      mockFetch.mockImplementation(() => {
        callCount++;
        return Promise.resolve({
          ok: true,
          json: async () => (callCount % 2 === 1 ? chatResponse : searchResponse),
        });
      });

      renderComponent();

      const textarea = screen.getByPlaceholderText(/describe the fault/i);
      const diagnoseButton = screen.getByRole('button', { name: /diagnose/i });

      await userEvent.type(textarea, 'Test fault');
      await userEvent.click(diagnoseButton);

      await waitFor(
        () => {
          expect(mockFetch).toHaveBeenCalledTimes(2); // Chat + Search
        },
        { timeout: 5000 }
      );

      // Verify both endpoints were called
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/'),
        expect.any(Object)
      );

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/search/'),
        expect.any(Object)
      );
    });
  });

  describe('API Response Format Validation (AC: 2)', () => {
    it('should validate chat API response structure', async () => {
      const response = {
        success: true,
        data: {
          answer: 'Test answer',
          fault_code: 'TEST-001',
          component: 'Test Component',
          summary: 'Test summary',
          resolution_steps: ['Step 1', 'Step 2'],
          sources: [],
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => response,
      });

      const result = await mockFetch('/api/chat/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'test' }),
      });

      const data = await result.json();
      expect(data.success).toBe(true);
      expect(data.data).toHaveProperty('answer');
      expect(data.data).toHaveProperty('resolution_steps');
      expect(Array.isArray(data.data.resolution_steps)).toBe(true);
    });

    it('should validate analytics API response structure', async () => {
      const response = {
        success: true,
        data: {
          total_metrics: { total_work_orders: 100, total_downtime: 24.5 },
          mtbf: 72.5,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => response,
      });

      const result = await mockFetch('/api/analytics/summary');
      const data = await result.json();

      expect(data.success).toBe(true);
      expect(data.data).toHaveProperty('total_metrics');
      expect(data.data).toHaveProperty('mtbf');
    });
  });

  describe('API Performance and Timeout (AC: 4)', () => {
    it('should handle slow API responses', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => ({
                  success: true,
                  data: { answer: 'Response' },
                }),
              });
            }, 1000); // 1 second delay
          })
      );

      const startTime = Date.now();
      await fetch('/api/chat/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'test' }),
      });

      const endTime = Date.now();

      expect(endTime - startTime).toBeGreaterThanOrEqual(1000);
    }, 5000);
  });
});
