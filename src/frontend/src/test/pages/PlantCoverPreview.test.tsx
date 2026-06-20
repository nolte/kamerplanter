import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import PlantCoverPreview from '@/pages/pflanzen/photos/PlantCoverPreview';

const TENANT = 'test-tenant';
const PLANT_KEY = 'plant-1';
const PHOTOS_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/photos`;

function photo(id: string) {
  const uri = `/api/v1/t/${TENANT}/attachments/${id}`;
  return {
    attachment_id: id,
    uri,
    thumbnail_uris: { small: `${uri}/thumbnails/128`, medium: `${uri}/thumbnails/512`, large: `${uri}/thumbnails/1280` },
    is_cover: id === 'cover',
    mime_type: 'image/jpeg',
    byte_size: 10,
    created_at: null,
  };
}

describe('PlantCoverPreview (REQ-034 §2.3 / AC-06)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the small cover thumbnail when a cover photo exists', async () => {
    server.use(
      http.get(PHOTOS_URL, () =>
        HttpResponse.json({ plant_instance_key: PLANT_KEY, cover_photo_ref: 'cover', photos: [photo('cover'), photo('b')] }),
      ),
    );
    renderWithProviders(<PlantCoverPreview plantInstanceKey={PLANT_KEY} />);

    const img = (await screen.findByTestId('plant-cover-image')) as HTMLImageElement;
    // AC-02: only the small (128px) rendition is loaded for previews.
    expect(img.src).toContain('/attachments/cover/thumbnails/128');
  });

  it('shows a neutral placeholder (never a broken image) when there are no photos', async () => {
    server.use(
      http.get(PHOTOS_URL, () =>
        HttpResponse.json({ plant_instance_key: PLANT_KEY, cover_photo_ref: null, photos: [] }),
      ),
    );
    renderWithProviders(<PlantCoverPreview plantInstanceKey={PLANT_KEY} />);

    await waitFor(() => expect(screen.getByTestId('plant-cover-placeholder')).toBeInTheDocument());
    expect(screen.queryByTestId('plant-cover-image')).not.toBeInTheDocument();
  });

  it('renders a pre-resolved cover URI without fetching', async () => {
    let fetched = false;
    server.use(
      http.get(PHOTOS_URL, () => {
        fetched = true;
        return HttpResponse.json({ plant_instance_key: PLANT_KEY, cover_photo_ref: null, photos: [] });
      }),
    );
    renderWithProviders(
      <PlantCoverPreview plantInstanceKey={PLANT_KEY} coverThumbUri="/api/v1/t/test-tenant/attachments/x/thumbnails/128" />,
    );

    const img = (await screen.findByTestId('plant-cover-image')) as HTMLImageElement;
    expect(img.src).toContain('/attachments/x/thumbnails/128');
    expect(fetched).toBe(false);
  });
});
