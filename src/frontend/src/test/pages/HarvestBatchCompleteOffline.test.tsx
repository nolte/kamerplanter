import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { setActiveTenantSlug } from '@/api/client';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'batch-1' }) };
});

import HarvestBatchDetailPage from '@/pages/ernte/HarvestBatchDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const T = '/api/v1/t/:tenant';

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

/**
 * #3025 N-39 (review c) — completing a harvest is a phase change the server validates (UI-NFR-012 R-020a/b).
 * The opener is locked offline, and a confirmation that was opened online does not fire once the connection
 * dropped.
 */
describe('HarvestBatchDetailPage — complete harvest offline', () => {
  const completes: unknown[] = [];

  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
    setOnline(true);
    completes.length = 0;
    server.use(
      http.get(`${T}/harvest/batches/:key`, () =>
        HttpResponse.json({
          key: 'batch-1',
          batch_id: 'HB-1',
          plant_key: 'plant-1',
          harvest_date: '2026-06-01',
          harvest_type: 'final',
          wet_weight_g: 100,
          estimated_dry_weight_g: null,
          actual_dry_weight_g: null,
          quality_grade: null,
          harvester: '',
          notes: null,
          created_at: null,
          updated_at: null,
        }),
      ),
      http.get(`${T}/harvest/batches/:key/quality`, () => HttpResponse.json(null)),
      http.get(`${T}/harvest/batches/:key/yield`, () => HttpResponse.json(null)),
      http.get(`${T}/plant-instances/:key`, () => HttpResponse.json({}, { status: 404 })),
      http.post(`${T}/harvest/plants/:plantKey/complete`, async ({ request }) => {
        completes.push(await request.json());
        return HttpResponse.json({ plant_key: 'plant-1' });
      }),
    );
  });

  afterEach(() => setOnline(true));

  it('locks the opener offline with the reason', async () => {
    renderWithProviders(<HarvestBatchDetailPage />);
    const opener = await screen.findByTestId('complete-harvest-button', {}, { timeout: 5000 });
    act(() => {
      setOnline(false);
      window.dispatchEvent(new Event('offline'));
    });
    expect(opener).toHaveAttribute('aria-disabled', 'true');
    expect(opener).toHaveAccessibleDescription('Netzwerkverbindung erforderlich');
  });

  it('does not send when the connection drops while the confirmation is open', async () => {
    const user = userEvent.setup();
    renderWithProviders(<HarvestBatchDetailPage />);
    await user.click(await screen.findByTestId('complete-harvest-button', {}, { timeout: 5000 }));
    const dialog = await screen.findByTestId('confirm-dialog');

    act(() => {
      setOnline(false);
      window.dispatchEvent(new Event('offline'));
    });
    await user.click(within(dialog).getByTestId('confirm-dialog-confirm'));
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(completes).toHaveLength(0);
  });
});
