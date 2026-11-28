import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, fireEvent, act } from '@testing-library/react';
import i18n from 'i18next';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import ConsentBanner from '@/components/privacy/ConsentBanner';
import {
  CONSENT_STORAGE_KEY,
  accountEpoch,
  readConsent,
  readConsentSnapshot,
  resetConsentStoreForTests,
  setAccountConsent,
  setAuthStatus,
} from '@/observability/consent';
import { server } from '../../mocks/server';
import { renderWithProviders } from '../../helpers';

const DSN = 'https://key@glitchtip.example.org/1';

function consentBody(granted: boolean) {
  return {
    purpose: 'browser_error_reports',
    label: 'Send error reports from the browser',
    description: '…',
    legal_basis: 'Art. 6(1)(a) GDPR',
    required: false,
    granted,
    granted_at: granted ? '2026-11-28T09:00:00Z' : null,
    revoked_at: granted ? null : '2026-11-28T09:00:00Z',
    consent_version: '1.0',
    purpose_version: '1.0',
  };
}

function signedInUndecided(): void {
  act(() => {
    setAuthStatus({ kind: 'signed_in', account: 'user-a' });
    setAccountConsent('user-a', { kind: 'undecided' }, accountEpoch());
  });
}

describe('UI-NFR-013 ConsentBanner', () => {
  beforeEach(() => {
    window.localStorage.clear();
    resetConsentStoreForTests();
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
  });

  afterEach(() => {
    window.localStorage.clear();
    resetConsentStoreForTests();
    delete window.__RUNTIME_CONFIG__;
  });

  it('does not render before the sign-in state is known (CP-008)', () => {
    renderWithProviders(<ConsentBanner />);
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  describe('device form (signed out)', () => {
    beforeEach(() => setAuthStatus({ kind: 'signed_out' }));

    it('renders with three equal-prominence actions and says it applies to this browser', () => {
      renderWithProviders(<ConsentBanner />);
      const banner = screen.getByTestId('consent-banner');
      expect(banner).toHaveAttribute('data-consent-form', 'device');
      expect(banner).toHaveTextContent(/nur für diesen Browser|this browser only/);
      for (const id of ['accept-all', 'necessary', 'settings']) {
        expect(screen.getByTestId(`consent-banner-${id}`)).toBeInTheDocument();
      }
    });

    it('stores "Alle akzeptieren" on the device only — no request leaves', () => {
      const posted = vi.fn();
      server.use(
        http.post('/api/v1/privacy/consents', () => {
          posted();
          return HttpResponse.json({}, { status: 201 });
        }),
      );
      const onChoice = vi.fn();
      renderWithProviders(<ConsentBanner onChoice={onChoice} />);

      fireEvent.click(screen.getByTestId('consent-banner-accept-all'));

      expect(readConsent().browser_error_reports).toBe(true);
      expect(onChoice).toHaveBeenCalledWith(true, 'all');
      expect(posted).not.toHaveBeenCalled();
      expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
    });

    it('declines with "Nur Notwendige"', () => {
      renderWithProviders(<ConsentBanner />);
      fireEvent.click(screen.getByTestId('consent-banner-necessary'));
      expect(readConsent().browser_error_reports).toBe(false);
    });

    it('stays hidden once this device decided (CB-006)', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, browser_error_reports: false, version: '1.0' }),
      );
      renderWithProviders(<ConsentBanner />);
      expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
    });

    it('asks once anew when only a grant from before v1.3 is stored (CP-005)', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, error_tracking: true, external_services: true }),
      );
      renderWithProviders(<ConsentBanner />);
      expect(screen.getByTestId('consent-banner')).toBeInTheDocument();
    });

    // CB-008 (#3025 F-4): recipient, content and IP note before anything is expanded.
    it('shows recipient host, content and the IP note without expanding (CB-008)', () => {
      renderWithProviders(<ConsentBanner />);
      expect(screen.getByTestId('consent-banner-categories')).not.toBeVisible();
      const visible = screen.getByTestId('consent-banner-summary');
      expect(visible).toBeVisible();
      expect(visible).toHaveTextContent('glitchtip.example.org');
      expect(visible).toHaveTextContent(/IP-Adresse|IP address/);
      expect(visible).toHaveTextContent(/keine Eingaben|no input/);
    });

    it('names the public way to take the decision back (CW-006)', () => {
      renderWithProviders(<ConsentBanner />);
      expect(screen.getByTestId('consent-banner')).toHaveTextContent(
        /Entscheidung dieses Browsers zu Fehlerberichten ändern|Change this browser's decision on error reports/,
      );
    });

    // CB-007 (#3025 F-3): no decision to a text that is not on screen.
    it('renders no decision controls while the consent texts are missing, and appears once they load', () => {
      let missing = true;
      const exists = i18n.exists.bind(i18n);
      const spy = vi
        .spyOn(i18n, 'exists')
        .mockImplementation(((key: string, options?: Parameters<typeof i18n.exists>[1]) =>
          missing && String(key).startsWith('consent.')
            ? false
            : exists(key, options)) as typeof i18n.exists);
      try {
        renderWithProviders(<ConsentBanner />);
        expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
        expect(screen.queryByRole('button')).not.toBeInTheDocument();

        missing = false;
        // The way a late feature bundle arrives (`loadFeatureNamespaces` -> addResourceBundle).
        act(() => {
          i18n.addResourceBundle('de', 'translation', {}, true, true);
        });
        expect(screen.getByTestId('consent-banner-accept-all')).toBeInTheDocument();
      } finally {
        spy.mockRestore();
      }
    });

    it('names what a report contains and where it goes, with the tracker host (CK-004)', () => {
      renderWithProviders(<ConsentBanner />);
      fireEvent.click(screen.getByTestId('consent-banner-settings'));
      const description = screen.getByRole('switch', {
        name: /Fehlerberichte aus dem Browser|Error reports from the browser/,
      });
      expect(description).toHaveAccessibleDescription(/glitchtip\.example\.org/);
      expect(description).toHaveAccessibleDescription(/Formulareingaben|form input/);
    });

    it('offers no "Externe Dienste" category any more (CK-003)', () => {
      renderWithProviders(<ConsentBanner />);
      fireEvent.click(screen.getByTestId('consent-banner-settings'));
      expect(screen.getAllByRole('switch')).toHaveLength(1);
      expect(screen.queryByText(/Externe Dienste|External services/)).not.toBeInTheDocument();
    });

    it('lets the user choose under "Einstellungen" and save (CB-004)', () => {
      const onChoice = vi.fn();
      renderWithProviders(<ConsentBanner onChoice={onChoice} />);
      expect(screen.getByTestId('consent-banner-categories')).not.toBeVisible();

      fireEvent.click(screen.getByTestId('consent-banner-settings'));
      expect(screen.getByTestId('consent-banner-categories')).toBeVisible();
      fireEvent.click(screen.getByRole('switch'));
      fireEvent.click(screen.getByTestId('consent-banner-save'));

      expect(onChoice).toHaveBeenCalledWith(true, 'custom');
      expect(readConsent().browser_error_reports).toBe(true);
    });

    it('gives "Nur Notwendige" the same visual weight as "Alle akzeptieren" (CB-003)', () => {
      renderWithProviders(<ConsentBanner />);
      expect(screen.getByTestId('consent-banner-necessary').className).toContain(
        'MuiButton-contained',
      );
      expect(screen.getByTestId('consent-banner-accept-all').className).toContain(
        'MuiButton-contained',
      );
    });

    it('keeps focus on "Einstellungen" and announces the expanded state', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ConsentBanner />);
      const settings = screen.getByTestId('consent-banner-settings');
      expect(settings).toHaveAttribute('aria-expanded', 'false');
      expect(settings.getAttribute('aria-controls')).toBe(
        screen.getByTestId('consent-banner-categories').id,
      );

      await user.click(settings);

      expect(settings).toHaveFocus();
      expect(settings).toHaveAttribute('aria-expanded', 'true');
    });

    it('is reachable and operable by keyboard alone', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ConsentBanner />);
      screen.getByTestId('consent-banner-settings').focus();

      await user.tab();
      expect(screen.getByTestId('consent-banner-necessary')).toHaveFocus();
      await user.keyboard('{Enter}');

      expect(readConsent().browser_error_reports).toBe(false);
    });
  });

  describe('account form (signed in, no account decision)', () => {
    it('does not render while the account is not read yet (no flash on a new device)', () => {
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
      renderWithProviders(<ConsentBanner />);
      expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
    });

    it('says the decision is stored in the account and grants through the API', async () => {
      const posted = vi.fn();
      server.use(
        http.post('/api/v1/privacy/consents', async ({ request }) => {
          posted(await request.json());
          return HttpResponse.json(consentBody(true), { status: 201 });
        }),
      );
      signedInUndecided();
      renderWithProviders(<ConsentBanner />);
      const banner = screen.getByTestId('consent-banner');
      expect(banner).toHaveAttribute('data-consent-form', 'account');
      expect(banner).toHaveTextContent(/in deinem Konto gespeichert|stored in your account/);

      fireEvent.click(screen.getByTestId('consent-banner-accept-all'));

      await vi.waitFor(() => expect(readConsentSnapshot().account.kind).toBe('granted'));
      expect(posted).toHaveBeenCalledWith({
        purpose: 'browser_error_reports',
        purpose_version: '1.0',
      });
      // The device decision is untouched: the click was the account's.
      expect(readConsent().browser_error_reports).toBeNull();
      expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
    });

    it('keeps the banner with an error and a retry when the grant fails (CP-012)', async () => {
      let fail = true;
      server.use(
        http.post('/api/v1/privacy/consents', () =>
          fail
            ? new HttpResponse(null, { status: 503 })
            : HttpResponse.json(consentBody(true), { status: 201 }),
        ),
      );
      signedInUndecided();
      renderWithProviders(<ConsentBanner />);

      fireEvent.click(screen.getByTestId('consent-banner-accept-all'));

      const alert = await screen.findByTestId('consent-banner-error');
      expect(alert).toHaveAttribute('role', 'alert');
      expect(readConsentSnapshot().account.kind).toBe('undecided');
      expect(screen.getByTestId('consent-banner-accept-all')).toHaveAccessibleDescription(
        /nicht in deinem Konto gespeichert|could not be stored/,
      );

      fail = false;
      fireEvent.click(screen.getByTestId('consent-banner-retry'));
      await vi.waitFor(() => expect(readConsentSnapshot().account.kind).toBe('granted'));
    });

    // CP-013 (#3025 F-2): a newer text on the server asks for a reload, never "could not be saved".
    it('asks for a reload when the server holds a newer text, and records nothing', async () => {
      server.use(
        http.post('/api/v1/privacy/consents', () =>
          HttpResponse.json(
            {
              error_id: 'e',
              error_code: 'CONSENT_TEXT_OUTDATED',
              message: 'changed',
              details: [],
              path: '/api/v1/privacy/consents',
              method: 'POST',
            },
            { status: 409 },
          ),
        ),
      );
      signedInUndecided();
      renderWithProviders(<ConsentBanner />);

      fireEvent.click(screen.getByTestId('consent-banner-accept-all'));

      const alert = await screen.findByTestId('consent-banner-outdated');
      expect(alert).toHaveTextContent(/lade die Seite neu|reload the page/);
      expect(screen.queryByTestId('consent-banner-error')).not.toBeInTheDocument();
      expect(screen.queryByTestId('consent-banner-accept-all')).not.toBeInTheDocument();
      expect(readConsentSnapshot().account.kind).toBe('outdated');
    });

    it('a decline stops at once even if the request fails, and says it is not stored yet', async () => {
      server.use(
        http.delete(
          '/api/v1/privacy/consents/:purpose',
          () => new HttpResponse(null, { status: 503 }),
        ),
      );
      signedInUndecided();
      renderWithProviders(<ConsentBanner />);

      fireEvent.click(screen.getByTestId('consent-banner-necessary'));

      expect(readConsentSnapshot().pendingRevoke).toBe(true);
      expect(
        await screen.findByText(/noch nicht in deinem Konto|not stored in your account/),
      ).toBeInTheDocument();
    });

    it('is not asked when this device declined (CP-007)', () => {
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, browser_error_reports: false, version: '1.0' }),
      );
      signedInUndecided();
      renderWithProviders(<ConsentBanner />);
      expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
    });
  });
});
