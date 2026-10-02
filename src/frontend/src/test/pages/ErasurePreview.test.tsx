import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { screen, within, cleanup, waitFor, renderHook } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import { useErasurePreview } from '@/hooks/useErasurePreview';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import dePages from '@/i18n/locales/de/pages.json';
import enPages from '@/i18n/locales/en/pages.json';

/**
 * REQ-025 AK-FK-06 (#1824) — before the person confirms the account deletion,
 * the dialog and the tab say which personal tenants go with it and how many
 * other members that affects. Erasure together means a shared personal garden is
 * deleted with its owner's account, so the confirmation has to name it.
 */

function previewResponse(tenants: { name: string; other_member_count: number }[]) {
  server.use(
    http.get('/api/v1/privacy/erasure-preview', () =>
      HttpResponse.json({ personal_tenants: tenants }),
    ),
  );
}

async function openPrivacyErasureTab() {
  const user = userEvent.setup();
  renderWithProviders(<PrivacySettingsPage />, { store: createTestStore(authState()) });
  await user.click(await screen.findByTestId('privacy-tab-erasure'));
  return user;
}

describe('erasure preview — privacy tab (AK-FK-06)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  it('names each personal tenant with the number of other members, before the dialog is opened', async () => {
    previewResponse([{ name: 'Ada', other_member_count: 2 }]);
    await openPrivacyErasureTab();

    const panel = await screen.findByTestId('privacy-erasure-preview');
    expect(within(panel).getByTestId('privacy-erasure-preview-tenant')).toHaveTextContent(
      '„Ada“ wird gelöscht, 2 weitere Mitglieder sind betroffen.',
    );
    // The consequence for the others is explained, not only counted.
    expect(within(panel).getByTestId('privacy-erasure-preview-shared-hint')).toBeInTheDocument();
  });

  it('uses the singular for one other member and omits the member part for none', async () => {
    previewResponse([
      { name: 'Ada', other_member_count: 1 },
      { name: 'Bee', other_member_count: 0 },
    ]);
    await openPrivacyErasureTab();

    const lines = await screen.findAllByTestId('privacy-erasure-preview-tenant');
    expect(lines.map((l) => l.textContent)).toEqual([
      '„Ada“ wird gelöscht, 1 weiteres Mitglied ist betroffen.',
      '„Bee“ wird gelöscht.',
    ]);
  });

  it('shows no hint about other members when nobody shares the tenant', async () => {
    previewResponse([{ name: 'Ada', other_member_count: 0 }]);
    await openPrivacyErasureTab();

    await screen.findByTestId('privacy-erasure-preview');
    expect(screen.queryByTestId('privacy-erasure-preview-shared-hint')).toBeNull();
  });

  it('shows nothing for an account without a personal tenant', async () => {
    previewResponse([]);
    await openPrivacyErasureTab();

    await screen.findByTestId('privacy-erasure-request-btn');
    await waitFor(() => expect(screen.queryByTestId('privacy-erasure-preview')).toBeNull());
    expect(screen.queryByTestId('privacy-erasure-preview-error')).toBeNull();
  });

  it('repeats the preview inside the confirmation dialog', async () => {
    previewResponse([{ name: 'Ada', other_member_count: 2 }]);
    const user = await openPrivacyErasureTab();
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));

    const dialog = await screen.findByTestId('privacy-erasure-dialog');
    expect(
      await within(dialog).findByTestId('privacy-erasure-dialog-preview-tenant'),
    ).toHaveTextContent('„Ada“ wird gelöscht, 2 weitere Mitglieder sind betroffen.');
  });

  it('says so when the preview cannot be read, instead of looking like "nothing is affected"', async () => {
    server.use(
      http.get('/api/v1/privacy/erasure-preview', () => new HttpResponse(null, { status: 500 })),
    );
    await openPrivacyErasureTab();

    expect(await screen.findByTestId('privacy-erasure-preview-error')).toHaveTextContent(
      'Deine persönlichen Gärten werden in jedem Fall mit allem Inhalt gelöscht',
    );
  });

  it('does not ask for the preview while another tab is open', async () => {
    let calls = 0;
    server.use(
      http.get('/api/v1/privacy/erasure-preview', () => {
        calls += 1;
        return HttpResponse.json({ personal_tenants: [] });
      }),
    );
    renderWithProviders(<PrivacySettingsPage />, { store: createTestStore(authState()) });
    await screen.findByTestId('privacy-tab-erasure');

    expect(calls).toBe(0);
  });
});

describe('erasure preview — account settings delete dialog (AK-FK-06)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  it('shows the preview in the delete-account dialog', async () => {
    previewResponse([{ name: 'Ada', other_member_count: 3 }]);
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#account',
    });
    await user.click(await screen.findByTestId('delete-account-btn'));

    const dialog = await screen.findByTestId('delete-account-dialog');
    expect(await within(dialog).findByTestId('delete-account-preview-tenant')).toHaveTextContent(
      '„Ada“ wird gelöscht, 3 weitere Mitglieder sind betroffen.',
    );
  });
});

describe('erasure preview — texts', () => {
  const keys = [
    'erasurePreviewHeading',
    'erasurePreviewTenantAlone',
    'erasurePreviewTenantShared_one',
    'erasurePreviewTenantShared_other',
    'erasurePreviewSharedHint',
    'erasurePreviewLoading',
    'erasurePreviewError',
  ];

  it.each([
    ['de', dePages],
    ['en', enPages],
  ])('has every key in %s', (_lang, pages) => {
    const privacy = (pages as unknown as { pages: { privacy: Record<string, string> } }).pages
      .privacy;
    expect(keys.filter((k) => !privacy[k])).toEqual([]);
  });
});

describe('useErasurePreview', () => {
  afterEach(cleanup);

  it('forgets the previous answer when it is closed and read again', async () => {
    previewResponse([{ name: 'Ada', other_member_count: 2 }]);
    const { result, rerender } = renderHook(({ on }) => useErasurePreview(on), {
      initialProps: { on: true },
    });
    expect(result.current.status).toBe('loading');
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.tenants[0].other_member_count).toBe(2);

    rerender({ on: false });
    expect(result.current.status).toBe('idle');
    expect(result.current.tenants).toEqual([]);

    previewResponse([{ name: 'Ada', other_member_count: 0 }]);
    rerender({ on: true });
    expect(result.current.status).toBe('loading');
    await waitFor(() => expect(result.current.tenants[0].other_member_count).toBe(0));
  });
});
