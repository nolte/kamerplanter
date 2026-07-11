import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ThemeContextProvider } from '@/theme';
import KioskStartPage from '@/pages/kiosk/KioskStartPage';
import { createTestStore, type TestStore } from '@/test/helpers';

function renderStartPage(store: TestStore) {
  const router = createMemoryRouter(
    [
      { path: '/kiosk', element: <KioskStartPage /> },
      { path: '/pflanzen/identifikation', element: <div data-testid="target-scan" /> },
      { path: '/giessprotokoll', element: <div data-testid="target-watering" /> },
      { path: '/aufgaben/queue', element: <div data-testid="target-round" /> },
      { path: '/pflanzenschutz/erkennung', element: <div data-testid="target-problem" /> },
    ],
    { initialEntries: ['/kiosk'] },
  );
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <RouterProvider router={router} />
      </ThemeContextProvider>
    </Provider>,
  );
}

describe('KioskStartPage (UI-NFR-019)', () => {
  it('renders the four required quick-action tiles (R-014, R-015)', () => {
    renderStartPage(createTestStore());
    expect(screen.getByTestId('kiosk-tile-scan')).toBeInTheDocument();
    expect(screen.getByTestId('kiosk-tile-watering')).toBeInTheDocument();
    expect(screen.getByTestId('kiosk-tile-round')).toBeInTheDocument();
    expect(screen.getByTestId('kiosk-tile-problem')).toBeInTheDocument();
  });

  it('renders the current-status panel with the open-task count (R-016)', () => {
    const store = createTestStore({
      tasks: {
        workflows: [],
        taskTemplates: [],
        tasks: [],
        currentTask: null,
        taskQueue: [{ key: 't1' }, { key: 't2' }],
        overdueTasks: [{ key: 'o1' }],
        loading: false,
        error: null,
      },
    });
    renderStartPage(store);
    const panel = screen.getByTestId('kiosk-status-panel');
    expect(panel).toHaveTextContent('2');
    expect(panel).toHaveTextContent('1');
  });

  it('navigates to the scan target when the scan tile is activated', async () => {
    const user = userEvent.setup();
    renderStartPage(createTestStore());
    await act(async () => {
      await user.click(screen.getByTestId('kiosk-tile-scan'));
    });
    expect(screen.getByTestId('target-scan')).toBeInTheDocument();
  });

  it('navigates to the watering target when the watering tile is activated', async () => {
    const user = userEvent.setup();
    renderStartPage(createTestStore());
    await act(async () => {
      await user.click(screen.getByTestId('kiosk-tile-watering'));
    });
    expect(screen.getByTestId('target-watering')).toBeInTheDocument();
  });
});
