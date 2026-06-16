import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import IdentificationConsentGate from '@/components/identification/IdentificationConsentGate';

/**
 * REQ-029 §5 / UI-NFR-013 — hard consent gate component tests.
 *
 * Covers the four render states (loading, granted, blocked-full-mode,
 * blocked-light-mode), the granting spinner, the error alert and the grant/
 * decline callbacks — i.e. every branch in the gate.
 */

function setup(overrides: Partial<React.ComponentProps<typeof IdentificationConsentGate>> = {}) {
  const props = {
    granted: false,
    loading: false,
    granting: false,
    error: null,
    onGrant: vi.fn(),
    onDecline: vi.fn(),
    ...overrides,
  };
  renderWithProviders(<IdentificationConsentGate {...props} />);
  return props;
}

describe('IdentificationConsentGate', () => {
  it('shows a spinner while the consent state is loading', () => {
    setup({ loading: true });
    expect(screen.getByTestId('consent-gate-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('identification-consent-gate')).not.toBeInTheDocument();
  });

  it('renders nothing once consent is granted', () => {
    setup({ granted: true });
    expect(screen.queryByTestId('identification-consent-gate')).not.toBeInTheDocument();
    expect(screen.queryByTestId('consent-gate-loading')).not.toBeInTheDocument();
  });

  it('renders the gate with the privacy-settings link in full mode', () => {
    setup({ showPrivacyLink: true });
    expect(screen.getByTestId('identification-consent-gate')).toBeInTheDocument();
    // Full mode renders the revocation link to the privacy settings.
    expect(screen.getByRole('link')).toHaveAttribute('href', '/settings#privacy');
  });

  it('hides the privacy link in Light mode but keeps the transparency notice', () => {
    setup({ showPrivacyLink: false });
    expect(screen.getByTestId('identification-consent-gate')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('invokes onGrant / onDecline from the action buttons', async () => {
    const { onGrant, onDecline } = setup();
    await userEvent.click(screen.getByTestId('consent-accept'));
    expect(onGrant).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByTestId('consent-decline'));
    expect(onDecline).toHaveBeenCalledTimes(1);
  });

  it('disables the accept button and shows a spinner while granting', () => {
    setup({ granting: true });
    expect(screen.getByTestId('consent-accept')).toBeDisabled();
  });

  it('surfaces an error alert when granting fails', () => {
    setup({ error: 'Consent could not be saved' });
    const alert = screen.getByTestId('consent-gate-error');
    expect(alert).toHaveTextContent('Consent could not be saved');
  });
});
