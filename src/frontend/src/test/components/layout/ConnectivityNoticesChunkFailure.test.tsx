import { describe, it, expect, vi } from 'vitest';
import { act, screen } from '@testing-library/react';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import { renderWithProviders } from '../../helpers';

/**
 * #3025 N-39 (review e) — the change snackbars are a lazy chunk of the always-mounted connectivity indicator.
 * A chunk that cannot be fetched (offline before it was cached, a deploy in between) must not throw into the
 * shell's error boundary: the indicator keeps showing the state and the notices are simply absent.
 */
vi.mock('@/components/layout/ConnectivityNotices', () => {
  throw new Error('Failed to fetch dynamically imported module');
});

describe('ConnectivityIndicator with an unloadable notices chunk', () => {
  it('keeps rendering the indicator', async () => {
    renderWithProviders(<ConnectivityIndicator />);
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(screen.getByTestId('connectivity-indicator')).toBeInTheDocument();
  });
});
