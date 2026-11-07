import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, screen } from '@testing-library/react';
import i18n from 'i18next';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import { renderWithProviders } from '../../helpers';

/**
 * UI-NFR-012 R-033–R-035 (REQ-053 WP 9.1) — the app shell's permanent online/offline indicator.
 *
 * The live region must be ONE element that survives the change: a screen reader announces a content
 * change inside an existing `role="status"`, not a region that was replaced by a new one.
 */

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

function goOffline() {
  act(() => {
    setOnline(false);
    window.dispatchEvent(new Event('offline'));
  });
}

describe('ConnectivityIndicator', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('shows the online state inside a polite status region', () => {
    renderWithProviders(<ConnectivityIndicator />);
    const region = screen.getByRole('status');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toHaveAttribute('data-online', 'true');
    expect(region).toHaveTextContent('Online');
  });

  it('keeps the SAME live region when going offline and only changes its content', () => {
    renderWithProviders(<ConnectivityIndicator />);
    const before = screen.getByRole('status');

    goOffline();
    const after = screen.getByRole('status');
    expect(after).toBe(before);
    expect(after).toHaveAttribute('data-online', 'false');
    expect(after).toHaveTextContent('Offline');
    expect(screen.getAllByRole('status')).toHaveLength(1);

    act(() => {
      setOnline(true);
      window.dispatchEvent(new Event('online'));
    });
    expect(screen.getByRole('status')).toBe(before);
    expect(before).toHaveTextContent('Online');
  });
});
