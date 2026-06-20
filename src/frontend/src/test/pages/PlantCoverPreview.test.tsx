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

/** Tiny valid blob body for mocked attachment responses. */
function attachmentBlob() {
  return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
    headers: { 'Content-Type': 'image/jpeg' },
  });
}

/**
 * Registers blob handlers for the gated attachment endpoints and records every
 * requested rendition path so tests can assert which size was loaded (AC-02).
 */
function mockAttachmentBlobs(): string[] {
  const requested: string[] = [];
  server.use(
    http.get(`/api/v1/t/${TENANT}/attachments/:id/thumbnails/:px`, ({ request }) => {
      requested.push(new URL(request.url).pathname);
      return attachmentBlob();
    }),
  );
  return requested;
}

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
    const requested = mockAttachmentBlobs();
    renderWithProviders(<PlantCoverPreview plantInstanceKey={PLANT_KEY} />);

    // The cover is rendered from an authenticated blob Object-URL, not a bare
    // <img src={attachmentUri}> (which could not carry the Bearer header).
    const img = (await screen.findByTestId('plant-cover-image')) as HTMLImageElement;
    await waitFor(() => expect(img.src).toMatch(/^blob:/));
    expect(img.src).not.toContain('/attachments/');

    // AC-02: only the small (128px) rendition of the cover photo is loaded.
    await waitFor(() => expect(requested.length).toBeGreaterThan(0));
    expect(requested.every((p) => p.includes('/attachments/cover/thumbnails/128'))).toBe(true);
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

  it('renders a pre-resolved cover URI without fetching the gallery list', async () => {
    let listFetched = false;
    server.use(
      http.get(PHOTOS_URL, () => {
        listFetched = true;
        return HttpResponse.json({ plant_instance_key: PLANT_KEY, cover_photo_ref: null, photos: [] });
      }),
    );
    const requested = mockAttachmentBlobs();
    renderWithProviders(
      <PlantCoverPreview plantInstanceKey={PLANT_KEY} coverThumbUri="/api/v1/t/test-tenant/attachments/x/thumbnails/128" />,
    );

    // The blob is rendered from the explicitly passed URI; the gallery list is
    // never queried, and only the small (128px) rendition of that URI is loaded.
    const img = (await screen.findByTestId('plant-cover-image')) as HTMLImageElement;
    await waitFor(() => expect(img.src).toMatch(/^blob:/));
    expect(listFetched).toBe(false);
    expect(requested.every((p) => p.includes('/attachments/x/thumbnails/128'))).toBe(true);
  });
});
