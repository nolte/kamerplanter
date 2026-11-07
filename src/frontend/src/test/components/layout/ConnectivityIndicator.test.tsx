import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, screen } from '@testing-library/react';
import i18n from 'i18next';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import { renderWithProviders } from '../../helpers';

/** UI-NFR-012 R-033–R-035 (REQ-053 WP 9.1) — the app shell's permanent online/offline indicator. */

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

describe('ConnectivityIndicator', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('shows the online state as a labelled status', () => {
    renderWithProviders(<ConnectivityIndicator />);
    const indicator = screen.getByTestId('connectivity-indicator');
    expect(indicator).toHaveAttribute('data-online', 'true');
    expect(screen.getByRole('status', { name: 'Online' })).toBeInTheDocument();
  });

  it('switches to the "Offline" chip when the browser goes offline, and back', () => {
    renderWithProviders(<ConnectivityIndicator />);
    act(() => {
      setOnline(false);
      window.dispatchEvent(new Event('offline'));
    });
    expect(screen.getByTestId('connectivity-indicator')).toHaveAttribute('data-online', 'false');
    expect(screen.getByRole('status')).toHaveTextContent('Offline');

    act(() => {
      setOnline(true);
      window.dispatchEvent(new Event('online'));
    });
    expect(screen.getByTestId('connectivity-indicator')).toHaveAttribute('data-online', 'true');
  });
});
