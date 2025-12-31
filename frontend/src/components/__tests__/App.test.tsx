import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { ThemeProvider } from '../../theme'
import { AppLayout } from '../../layouts/AppLayout'
import Workbench from '../../pages/Workbench'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

describe('App Component Tests', () => {
  const renderWithProviders = (ui: React.ReactElement, route = '/') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={ThemeProvider}>
          <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
        </ConfigProvider>
      </QueryClientProvider>
    )
  }

  it('renders AppLayout without crashing', () => {
    renderWithProviders(<AppLayout />)
    const sidebar = document.querySelector('.ant-layout-sider')
    expect(sidebar).toBeInTheDocument()
  })

  it('renders Workbench page', () => {
    renderWithProviders(<Workbench />)
    expect(document.body.textContent).toContain('Diagnostic Workbench')
  })
})
