import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import ConsentBanner, { type ConsentState } from '@/components/privacy/ConsentBanner';
import { renderWithProviders } from '../../helpers';

const PENDING_STATE: ConsentState = {
  necessary: true,
  error_tracking: null,
  external_services: null,
  timestamp: null,
  version: '1.0',
};

const DECIDED_STATE: ConsentState = {
  necessary: true,
  error_tracking: false,
  external_services: false,
  timestamp: '2026-04-29T12:00:00Z',
  version: '1.0',
};

describe('UI-NFR-013 ConsentBanner', () => {
  beforeEach(() => {
    try {
      window.localStorage?.removeItem('kamerplanter:consent:v1');
    } catch {
      /* private mode / mock store — ignore */
    }
  });

  it('renders with three equal-prominence actions when no decision was made', () => {
    renderWithProviders(<ConsentBanner initialState={PENDING_STATE} />);
    expect(screen.getByTestId('consent-banner')).toBeInTheDocument();
    expect(screen.getByTestId('consent-banner-accept-all')).toBeInTheDocument();
    expect(screen.getByTestId('consent-banner-necessary')).toBeInTheDocument();
    expect(screen.getByTestId('consent-banner-settings')).toBeInTheDocument();
  });

  it('does not render when the user already decided', () => {
    renderWithProviders(<ConsentBanner initialState={DECIDED_STATE} />);
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('does not render in suppressed mode (REQ-027 light mode)', () => {
    renderWithProviders(<ConsentBanner initialState={PENDING_STATE} suppress />);
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('calls onChoice with all consents granted when "Alle akzeptieren" is clicked', () => {
    const onChoice = vi.fn();
    renderWithProviders(<ConsentBanner initialState={PENDING_STATE} onChoice={onChoice} />);
    fireEvent.click(screen.getByTestId('consent-banner-accept-all'));
    expect(onChoice).toHaveBeenCalledOnce();
    const [state, choice] = onChoice.mock.calls[0]!;
    expect(state.error_tracking).toBe(true);
    expect(state.external_services).toBe(true);
    expect(state.necessary).toBe(true);
    expect(state.timestamp).not.toBeNull();
    expect(choice).toBe('all');
  });

  it('declines optional categories when "Nur Notwendige" is clicked', () => {
    const onChoice = vi.fn();
    renderWithProviders(<ConsentBanner initialState={PENDING_STATE} onChoice={onChoice} />);
    fireEvent.click(screen.getByTestId('consent-banner-necessary'));
    const [state] = onChoice.mock.calls[0]!;
    expect(state.error_tracking).toBe(false);
    expect(state.external_services).toBe(false);
    expect(state.necessary).toBe(true);
  });

  it('renders a fresh banner without an initial state when localStorage is empty', () => {
    // localStorage is shimmed away in this test env; component falls through to
    // the default INITIAL_STATE and the banner shows up.
    renderWithProviders(<ConsentBanner />);
    expect(screen.getByTestId('consent-banner')).toBeInTheDocument();
  });
});
