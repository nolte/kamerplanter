/**
 * The botanical-family mutations are offered only to platform admins (#1155).
 *
 * #1120 made `POST/PUT/DELETE /botanical-families` platform-admin-only. The API
 * was right and the UI had not caught up: an ordinary member could open the
 * create dialog, fill in every field, submit — and learn only then that they may
 * not. The same for delete and save on the detail page.
 *
 * These are UX assertions, not security ones. The API refuses regardless of what
 * renders here, and nothing in this file would notice if that gate were removed;
 * `tests/e2e/test_req001_botanical_family.py` covers the refusal itself. What is
 * asserted here is that the dead end is gone in both directions — which needs
 * both halves, because a gate that hides the button from *everyone* also removes
 * the dead end and is equally wrong.
 */

import { screen } from '@testing-library/react';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import type { BotanicalFamily } from '@/api/types';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'bf-1' }) };
});

import BotanicalFamilyDetailPage from '@/pages/stammdaten/BotanicalFamilyDetailPage';
import BotanicalFamilyListPage from '@/pages/stammdaten/BotanicalFamilyListPage';

import { createTestStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/** Only `auth.user.is_platform_admin` is read by `usePlatformAdmin`. */
function storeFor(isPlatformAdmin: boolean) {
  return createTestStore({
    auth: {
      user: { is_platform_admin: isPlatformAdmin },
      isAuthenticated: true,
      isLoading: false,
    },
  });
}

/**
 * A complete `BotanicalFamily`, not a partial cast to one.
 *
 * The first attempt cast a four-field object, and `tsc` rejected it. It was
 * right to: the detail page renders every one of these fields, so a fixture
 * missing them would exercise a shape the API can never return — the page would
 * take its undefined-value branches and the test would certify those instead.
 *
 * No `as BotanicalFamily` either, for the same reason one step further out: the
 * cast is what let the wrong shape through in the first place, and leaving it
 * would silently absorb the next field this type gains.
 */
function family(): BotanicalFamily {
  return {
    key: 'bf-1',
    name: 'Lamiaceae',
    common_name_de: 'Lippenblütler',
    common_name_en: 'Mint family',
    order: 'Lamiales',
    description: 'Aromatische Kräuter mit vierkantigem Stängel.',
    typical_nutrient_demand: 'medium',
    nitrogen_fixing: false,
    typical_root_depth: 'medium',
    soil_ph_preference: { min_ph: 6.0, max_ph: 7.5 },
    frost_tolerance: 'hardy',
    typical_growth_forms: ['herb'],
    common_pests: [],
    common_diseases: [],
    pollination_type: ['insect'],
    rotation_category: 'mittelzehrer',
    species_count: 3,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: null,
  };
}

describe('Botanical families — platform-admin gate', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/botanical-families', () => HttpResponse.json([family()])),
      http.get('/api/v1/botanical-families/:key', () => HttpResponse.json(family())),
      http.get('/api/v1/species', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/species', () => HttpResponse.json([])),
    );
  });

  describe('list page', () => {
    it('offers "create" to a platform admin', async () => {
      renderWithProviders(<BotanicalFamilyListPage />, { store: storeFor(true) });

      expect(await screen.findByTestId('create-button')).toBeInTheDocument();
    });

    it('does not offer "create" to an ordinary member', async () => {
      renderWithProviders(<BotanicalFamilyListPage />, { store: storeFor(false) });

      // Waited for, not asserted immediately: the page renders its table
      // asynchronously, and a `queryBy` on the first frame is satisfied by the
      // button simply not having been rendered *yet* — true of the admin case too.
      expect(await screen.findByText('Lamiaceae')).toBeInTheDocument();
      expect(screen.queryByTestId('create-button')).not.toBeInTheDocument();
    });
  });

  describe('detail page', () => {
    it('offers delete and save to a platform admin', async () => {
      renderWithProviders(<BotanicalFamilyDetailPage />, { store: storeFor(true) });

      expect(await screen.findByRole('button', { name: /löschen/i })).toBeInTheDocument();
      expect(screen.queryByTestId('edit-denied-note')).not.toBeInTheDocument();
    });

    it('replaces them with an explanation for an ordinary member', async () => {
      renderWithProviders(<BotanicalFamilyDetailPage />, { store: storeFor(false) });

      // The explanation is the anchor: it renders with the form, so finding it
      // proves the page got past loading — the state in which no button exists
      // for reasons that have nothing to do with the gate.
      expect(await screen.findByTestId('edit-denied-note')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /löschen/i })).not.toBeInTheDocument();
    });
  });
});
