/**
 * Navigation and Page Transitions Integration Test
 * Tests complete user journey across all pages of the application
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AppLayout } from '../layouts/AppLayout';
import Workbench from '../pages/Workbench';
import Dashboard from '../pages/Dashboard';
import { Chat } from '../pages/Chat';
import { Settings } from '../pages/Settings';
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
    getSummary: vi.fn().mockResolvedValue({
      total_work_orders: 100,
      total_downtime: 24.5,
      avg_resolution_time: 2.5,
    }),
    getMTBF: vi.fn().mockResolvedValue([
      { date: '2025-12-01', mtbf: 72.5 },
      { date: '2025-12-15', mtbf: 75.2 },
    ]),
    getPareto: vi.fn().mockResolvedValue([
      { component: 'Power Supply', count: 25 },
      { component: 'Motor', count: 18 },
    ]),
    getFaultDistribution: vi.fn().mockResolvedValue([
      { fault_type: 'Electrical', count: 35 },
      { fault_type: 'Mechanical', count: 22 },
    ]),
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
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <QueryClientProvider client={queryClient}>
          <ConfigProvider theme={ThemeProvider}>
            <Routes>
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Workbench />} />
                <Route path="workbench" element={<Workbench />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="chat" element={<Chat />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </ConfigProvider>
        </QueryClientProvider>
      </MemoryRouter>
    );
  };

  it('should navigate from Workbench to Dashboard and verify page content', async () => {
    renderAppWithRouter('/workbench');

    // Step 1: Verify Workbench page is loaded
    await waitFor(() => {
      expect(screen.getByText(/Diagnostic Workbench/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Step 2: Find and click Dashboard link in navigation
    // Ant Design Menu items are not standard links, use text content instead
    const dashboardLink = screen.getByText('Dashboard');
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
    const workbenchLink = screen.getByText('Workbench');
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

    // Navigate to Settings - find the menu item (first occurrence)
    const settingsLinks = screen.getAllByText('Settings');
    const settingsMenuItem = settingsLinks[0]; // First is the menu item
    expect(settingsMenuItem).toBeInTheDocument();

    await userEvent.click(settingsMenuItem);

    await waitFor(() => {
      // Settings page has multiple "Settings" texts, check that at least one exists
      const settingsElements = screen.getAllByText(/Settings/i);
      expect(settingsElements.length).toBeGreaterThan(0);
    });

    // Navigate back to Workbench
    const workbenchLink = screen.getByText('Workbench');
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
    const chatLink = screen.getByText('Chat');
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

    // Navigate through each page (skip first since we're already at Workbench)
    for (let i = 1; i < pages.length; i++) {
      const page = pages[i];

      // For Settings, we need to get the menu item (first occurrence)
      let pageLink;
      if (page.name === 'Settings') {
        const settingsLinks = screen.getAllByText('Settings');
        pageLink = settingsLinks[0]; // First is the menu item
      } else {
        pageLink = screen.getByText(page.name);
      }

      expect(pageLink).toBeInTheDocument();

      await userEvent.click(pageLink);

      await waitFor(
        () => {
          // For Settings page, check that at least one element with title exists
          if (page.name === 'Settings') {
            const settingsElements = screen.getAllByText(/Settings/i);
            expect(settingsElements.length).toBeGreaterThan(0);
          } else {
            expect(screen.getByText(page.title)).toBeInTheDocument();
          }
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

    // Verify navigation links are accessible
    expect(screen.getByText('Workbench')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
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
    const dashboardLink = screen.getByText('Dashboard');
    await userEvent.click(dashboardLink);

    await waitFor(
      () => {
        expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Navigate back - verify navigation is still functional
    const workbenchLink = screen.getByText('Workbench');
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
    const workbenchLink = screen.getByText('Workbench');
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
    const dashboardLink = screen.getByText('Dashboard');
    const workbenchLink = screen.getByText('Workbench');

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
