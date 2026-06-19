import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ReferenceImageGallery from '@/pages/stammdaten/ReferenceImageGallery';
import { createTestStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/** Store with a platform-admin profile so the gallery shows the curation view. */
function adminStore() {
  return createTestStore({
    auth: {
      user: { key: 'u1', is_platform_admin: true },
      accessToken: 't',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    },
  });
}

const CURATION_URL = '/api/v1/admin/reference-images/sp-1/images';

function curationPayload(images: unknown[]) {
  const active = images.filter((i) => (i as { is_active: boolean }).is_active).length;
  return { species_key: 'sp-1', count: images.length, active_count: active, images };
}

describe('ReferenceImageCuration (admin)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders all images incl. deselected ones for a platform admin', async () => {
    server.use(
      http.get(CURATION_URL, () =>
        HttpResponse.json(
          curationPayload([
            { id: 1, source_url: 'https://x/1.jpg', license: 'CC-BY', attribution: 'Jane', organ: 'leaf', is_active: true },
            { id: 2, source_url: 'https://x/2.jpg', license: 'CC0', organ: 'flower', is_active: false, exclusion_reason: 'blurry' },
          ]),
        ),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" scientificName="Monstera deliciosa" />, {
      store: adminStore(),
    });

    await waitFor(() => {
      expect(screen.getAllByTestId('curation-image-item').length).toBe(2);
    });
    // The deselected image carries the badge.
    expect(screen.getByText('Abgewählt')).toBeTruthy();
  });

  it('deselects an active image with a reason and removes it from recognition', async () => {
    let patched: { is_active: boolean; reason: string | null } | null = null;
    server.use(
      http.get(CURATION_URL, () =>
        HttpResponse.json(
          curationPayload([
            { id: 1, source_url: 'https://x/1.jpg', organ: 'leaf', is_active: true },
          ]),
        ),
      ),
      http.patch('/api/v1/admin/reference-images/sp-1/images/1', async ({ request }) => {
        patched = (await request.json()) as { is_active: boolean; reason: string | null };
        return HttpResponse.json({ species_key: 'sp-1', id: 1, is_active: false });
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" scientificName="Monstera deliciosa" />, {
      store: adminStore(),
    });

    await screen.findByTestId('reference-deselect-button');
    await user.click(screen.getByTestId('reference-deselect-button'));

    // Dialog with a reason select appears.
    const dialog = await screen.findByTestId('deselect-dialog');
    await user.click(within(dialog).getByTestId('deselect-confirm'));

    await waitFor(() => {
      expect(patched).toEqual({ is_active: false, reason: 'blurry' });
    });
    // Tile flips to deselected (badge shown).
    await screen.findByText('Abgewählt');
  });

  it('renders a source link per image pointing at the original', async () => {
    server.use(
      http.get(CURATION_URL, () =>
        HttpResponse.json(
          curationPayload([
            { id: 1, source_url: 'https://x/1.jpg', is_active: true },
          ]),
        ),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" />, { store: adminStore() });

    const link = (await screen.findByTestId('reference-source-link')) as HTMLAnchorElement;
    expect(link.getAttribute('href')).toBe('https://x/1.jpg');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toContain('noopener');
  });

  it('hides deselected images when the toggle is switched on', async () => {
    server.use(
      http.get(CURATION_URL, () =>
        HttpResponse.json(
          curationPayload([
            { id: 1, source_url: 'https://x/1.jpg', is_active: true },
            { id: 2, source_url: 'https://x/2.jpg', is_active: false },
          ]),
        ),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" />, { store: adminStore() });

    await waitFor(() => {
      expect(screen.getAllByTestId('curation-image-item').length).toBe(2);
    });

    await user.click(screen.getByTestId('curation-hide-deselected-toggle'));

    await waitFor(() => {
      expect(screen.getAllByTestId('curation-image-item').length).toBe(1);
    });
    // The deselected badge is gone once its tile is hidden.
    expect(screen.queryByText('Abgewählt')).toBeNull();
  });

  it('warns when fewer than five reference images remain active', async () => {
    server.use(
      http.get(CURATION_URL, () =>
        HttpResponse.json(
          curationPayload([
            { id: 1, source_url: 'https://x/1.jpg', is_active: true },
            { id: 2, source_url: 'https://x/2.jpg', is_active: false },
          ]),
        ),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" />, { store: adminStore() });

    expect(await screen.findByTestId('curation-coverage-warning')).toBeTruthy();
  });
});
