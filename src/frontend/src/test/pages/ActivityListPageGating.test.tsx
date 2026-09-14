import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ActivityListPage from '@/pages/stammdaten/ActivityListPage';
import { createPlatformAdminStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * The activity catalogue is installation-wide and `POST /activities` carries
 * `require_platform_admin` since #1402 C.
 *
 * This file exists because the detail page's edit and delete were gated in that
 * change and the list page's create was not — the two halves of one catalogue
 * disagreeing, found in review round 2. The create affordance and the edit/delete
 * ones answer the same 403, so they belong to the same predicate.
 *
 * Both directions are asserted. An absence assertion alone would also hold if the
 * page failed to render at all, so the admin case is the control that proves the
 * button is findable when it should be there.
 */
describe('ActivityListPage — the create affordance follows the backend gate', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/activities', () =>
        HttpResponse.json([
          {
            key: 'act-1',
            name: 'Topping',
            name_de: 'Topping',
            description: '',
            description_de: '',
            is_system: true,
            species_compatible: [],
            tools_required: [],
            tags: [],
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
          },
        ]),
      ),
    );
  });

  it('offers the create button to a platform admin', async () => {
    renderWithProviders(<ActivityListPage />, { store: createPlatformAdminStore() });

    expect(await screen.findByText('Topping')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.activities.create'))).toBeInTheDocument();
  });

  it('withholds it from everyone else while the catalogue still reads', async () => {
    renderWithProviders(<ActivityListPage />);

    // Control: the list rendered and did its read.
    expect(await screen.findByText('Topping')).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('pages.activities.create'))).toBeNull();
  });
});
