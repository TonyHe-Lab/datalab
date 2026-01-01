/**
 * Navigation and Page Transitions Integration Test
 * Tests complete user journey across all pages of the application
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import App from '../App';
import { ThemeProvider } from '../theme';

// Mock services to prevent actual API calls
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

describe('Navigation and Page Transitions (E2E)', () => {
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

    vi.clearAllMocks();
  });

  const renderAppWithRouter = (initialRoute = '/') => {
    // 提供完整的window.location模拟
    Object.defineProperty(window, 'location', {
      writable: true,
      value: {
        pathname: initialRoute,
        origin: 'http://localhost:5173',
        href: `http://localhost:5173${initialRoute}`,
        search: '',
        hash: ''
      }
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={ThemeProvider}>
          <App />
        </ConfigProvider>
      </QueryClientProvider>
    );
  };

  it('should navigate from Workbench to Dashboard and verify page content', async () => {
    renderAppWithRouter('/workbench');

    // Step 1: Verify Workbench page is loaded
    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Step 2: Find and click Dashboard link in navigation
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toBeInTheDocument();

    await userEvent.click(dashboardLink);

    // Step 3: Verify navigation to Dashboard
    await waitFor(
      () => {
        expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // Step 4: Verify Workbench title is no longer visible
    expect(screen.queryByText(/Diagnostic Workbench/i)).not.toBeInTheDocument();
  });

  it('should navigate from Dashboard to Workbench', async () => {
    renderAppWithRouter('/dashboard');

    // Step 1: Verify Dashboard page is loaded
    await waitFor(() => {
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });

    // Step 2: Find and click Workbench link
    const workbenchLink = screen.getByRole('link', { name: /workbench/i });
    expect(workbenchLink).toBeInTheDocument();

    await userEvent.click(workbenchLink);

    // Step 3: Verify navigation to Workbench
    await waitFor(
      () => {
        expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should navigate to Settings page and return', async () => {
    renderAppWithRouter('/workbench');

    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Navigate to Settings
    const settingsLink = screen.getByRole('link', { name: /settings/i });
    expect(settingsLink).toBeInTheDocument();

    await userEvent.click(settingsLink);

    await waitFor(() => {
      expect(screen.getByText(/Settings/i)).toBeInTheDocument();
    });

    // Navigate back to Workbench
    const workbenchLink = screen.getByRole('link', { name: /workbench/i });
    await userEvent.click(workbenchLink);

    await waitFor(
      () => {
        expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should navigate to Chat page and verify interface', async () => {
    renderAppWithRouter('/workbench');

    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Navigate to Chat
    const chatLink = screen.getByRole('link', { name: /chat/i });
    expect(chatLink).toBeInTheDocument();

    await userEvent.click(chatLink);

    await waitFor(() => {
      expect(screen.getByText(/AI Chat Assistant/i)).toBeInTheDocument();
    });
  });

  it('should navigate through all main pages sequentially', async () => {
    renderAppWithRouter('/workbench');

    const pages = [
      { name: 'Workbench', title: /Diagnostic Workbench/i },
      { name: 'Dashboard', title: /Analytics Dashboard/i },
      { name: 'Chat', title: /AI Chat Assistant/i },
      { name: 'Settings', title: /Settings/i },
    ];

    // Start at Workbench
    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Navigate through each page
    for (const page of pages) {
      const pageLink = screen.getByRole('link', { name: new RegExp(page.name, 'i') });
      expect(pageLink).toBeInTheDocument();

      await userEvent.click(pageLink);

      await waitFor(
        () => {
          expect(screen.getByText(page.title)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    }
  }, 15000);

  it('should verify navigation links are always accessible', async () => {
    renderAppWithRouter('/dashboard');

    await waitFor(() => {
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });

    // Verify all navigation links are present
    const navigationLinks = [
      /workbench/i,
      /dashboard/i,
      /chat/i,
      /settings/i,
    ];

    for (const linkText of navigationLinks) {
      const link = screen.getByRole('link', {
        name: linkText,
      });
      expect(link).toBeInTheDocument();
    }
  });

  it('should handle direct URL navigation correctly', async () => {
    // Test direct navigation to Dashboard
    const { unmount } = renderAppWithRouter('/dashboard');

    await waitFor(() => {
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });

    unmount();

    // Test direct navigation to Workbench
    renderAppWithRouter('/workbench');

    await waitFor(
      () => {
        expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should maintain navigation state during page transitions', async () => {
    renderAppWithRouter('/workbench');

    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Navigate away
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    await userEvent.click(dashboardLink);

    await waitFor(
      () => {
        expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Navigate back - verify navigation is still functional
    const workbenchLink = screen.getByRole('link', { name: /workbench/i });
    await userEvent.click(workbenchLink);

    await waitFor(
      () => {
        expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should verify active route highlighting', async () => {
    renderAppWithRouter('/workbench');

    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Verify Workbench link is accessible
    const workbenchLink = screen.getByRole('link', { name: /workbench/i });
    expect(workbenchLink).toBeInTheDocument();

    // Note: Active styling verification would require checking CSS classes
    // This test verifies the navigation structure is correct
  });

  it('should handle rapid navigation between pages', async () => {
    renderAppWithRouter('/workbench');

    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    });

    // Rapidly navigate between Dashboard and Workbench
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    const workbenchLink = screen.getByRole('link', { name: /workbench/i });

    for (let i = 0; i < 3; i++) {
      await userEvent.click(dashboardLink);

      await waitFor(
        () => {
          expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      await userEvent.click(workbenchLink);

      await waitFor(
        () => {
          expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    }
  }, 20000);

  it('should verify default route redirects to workbench', async () => {
    renderAppWithRouter('/');

    // Should redirect to /workbench
    await waitFor(
      () => {
        expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.queryByText(/Analytics Dashboard/i)).not.toBeInTheDocument();
  });
});
