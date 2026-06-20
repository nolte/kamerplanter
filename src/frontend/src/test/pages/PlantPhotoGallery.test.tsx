import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, type TestStore } from '@/test/helpers';
import type { TenantRole } from '@/api/types';
import PlantPhotoGallery from '@/pages/pflanzen/photos/PlantPhotoGallery';

// The capture panel relies on canvas/getUserMedia (not available in jsdom), so
// it is mocked to a single button that synchronously hands a file to the dialog.
vi.mock('@/components/identification/ImageCapturePanel', () => ({
  default: ({ onImageReady }: { onImageReady: (f: File, url: string) => void }) => (
    <button
      type="button"
      data-testid="mock-pick-image"
      onClick={() =>
        onImageReady(new File([new Uint8Array([1, 2, 3])], 'p.jpg', { type: 'image/jpeg' }), 'blob:preview')
      }
    >
      pick
    </button>
  ),
}));

const PLANT_KEY = 'plant-1';
const TENANT = 'test-tenant';
const PHOTOS_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/photos`;
// AuthImage fetches every rendition through the authenticated client as a blob.
const ATTACHMENT_THUMB_URL = `/api/v1/t/${TENANT}/attachments/:id/thumbnails/:px`;

/** Tiny valid blob body for mocked attachment (thumbnail/original) responses. */
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
    http.get(ATTACHMENT_THUMB_URL, ({ request }) => {
      requested.push(new URL(request.url).pathname);
      return attachmentBlob();
    }),
    http.get(`/api/v1/t/${TENANT}/attachments/:id`, ({ request }) => {
      requested.push(new URL(request.url).pathname);
      return attachmentBlob();
    }),
  );
  return requested;
}

function photo(id: string, isCover = false) {
  const uri = `/api/v1/t/${TENANT}/attachments/${id}`;
  return {
    attachment_id: id,
    uri,
    thumbnail_uris: {
      small: `${uri}/thumbnails/128`,
      medium: `${uri}/thumbnails/512`,
      large: `${uri}/thumbnails/1280`,
    },
    is_cover: isCover,
    mime_type: 'image/jpeg',
    byte_size: 1234,
    created_at: '2026-06-19T10:00:00Z',
  };
}

function storeWithRole(role: TenantRole): TestStore {
  return createTestStore({
    tenants: {
      activeTenant: {
        key: 't1',
        name: 'Test',
        slug: TENANT,
        tenant_type: 'personal',
        description: null,
        avatar_url: null,
        owner_key: 'u1',
        max_members: 5,
        created_at: null,
        updated_at: null,
        role,
      },
      myTenants: [],
      isLoading: false,
      error: null,
    },
  });
}

function mockList(photos: ReturnType<typeof photo>[], cover: string | null = null) {
  server.use(
    http.get(PHOTOS_URL, () =>
      HttpResponse.json({
        plant_instance_key: PLANT_KEY,
        cover_photo_ref: cover ?? (photos[0]?.attachment_id ?? null),
        photos,
      }),
    ),
  );
}

describe('PlantPhotoGallery (REQ-034 §2.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('renders a thumbnail grid from the mocked gallery API (AC-02 medium thumbs)', async () => {
    mockList([photo('a', true), photo('b')], 'a');
    const requested = mockAttachmentBlobs();
    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getAllByTestId('plant-photo-item')).toHaveLength(2));
    // The thumbnails are rendered from authenticated blob Object-URLs, never a
    // bare <img src={attachmentUri}> (which could not send the Bearer header).
    const imgs = (await screen.findAllByTestId('plant-photo-image')) as HTMLImageElement[];
    await waitFor(() => expect(imgs[0].src).toMatch(/^blob:/));
    imgs.forEach((img) => expect(img.src).not.toContain('/attachments/'));

    // AC-02: the grid loads the medium (512px) rendition only — never the
    // original or the large (1280px) rendition.
    await waitFor(() => expect(requested.length).toBeGreaterThan(0));
    expect(requested.every((p) => p.includes('/thumbnails/512'))).toBe(true);
    expect(requested.some((p) => p.includes('/thumbnails/1280'))).toBe(false);
    expect(requested.some((p) => /\/attachments\/[^/]+$/.test(p))).toBe(false);

    // The cover photo carries its badge.
    expect(screen.getByTestId('plant-photo-cover-badge')).toBeInTheDocument();
  });

  it('shows an empty state with an upload CTA when there are no photos', async () => {
    mockList([]);
    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getByTestId('empty-state')).toBeInTheDocument());
    expect(screen.getByText('Noch keine Fotos')).toBeInTheDocument();
  });

  it('uploads a photo through the capture flow and refreshes the gallery (AC-01)', async () => {
    const user = userEvent.setup();
    let uploaded = false;
    server.use(
      http.get(PHOTOS_URL, () =>
        HttpResponse.json({
          plant_instance_key: PLANT_KEY,
          cover_photo_ref: uploaded ? 'new' : null,
          photos: uploaded ? [photo('new', true)] : [],
        }),
      ),
      http.post(PHOTOS_URL, () => {
        uploaded = true;
        return HttpResponse.json(photo('new', true), { status: 201 });
      }),
    );

    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getByTestId('empty-state')).toBeInTheDocument());
    await user.click(screen.getByTestId('plant-photo-add-button'));
    await user.click(await screen.findByTestId('mock-pick-image'));
    await user.click(screen.getByTestId('plant-photo-upload-confirm'));

    await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
  });

  it('surfaces a quota error (409 PHOTO_QUOTA_EXCEEDED) understandably (AC-15)', async () => {
    const user = userEvent.setup();
    mockList([]);
    server.use(
      http.post(PHOTOS_URL, () =>
        HttpResponse.json(
          {
            error_id: 'e1',
            error_code: 'PHOTO_QUOTA_EXCEEDED',
            message: 'quota',
            details: [],
            path: PHOTOS_URL,
            method: 'POST',
          },
          { status: 409 },
        ),
      ),
    );

    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getByTestId('empty-state')).toBeInTheDocument());
    await user.click(screen.getByTestId('plant-photo-add-button'));
    await user.click(await screen.findByTestId('mock-pick-image'));
    await user.click(screen.getByTestId('plant-photo-upload-confirm'));

    const alert = await screen.findByTestId('plant-photo-upload-error');
    expect(alert).toHaveTextContent(/Fotolimit/);
  });

  it('sets a cover photo via the API (AC-06)', async () => {
    const user = userEvent.setup();
    mockList([photo('a', true), photo('b')], 'a');
    const coverCall = vi.fn();
    server.use(
      http.put(`${PHOTOS_URL}/b/cover`, () => {
        coverCall();
        return HttpResponse.json({
          plant_instance_key: PLANT_KEY,
          cover_photo_ref: 'b',
          photos: [photo('a'), photo('b', true)],
        });
      }),
    );

    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getAllByTestId('plant-photo-item')).toHaveLength(2));
    // The non-cover photo (b) exposes a "set cover" button.
    const setCoverButtons = screen.getAllByTestId('plant-photo-set-cover');
    await user.click(setCoverButtons[0]);
    await waitFor(() => expect(coverCall).toHaveBeenCalledTimes(1));
  });

  it('deletes a photo only after confirmation (AC-07)', async () => {
    const user = userEvent.setup();
    mockList([photo('a', true)], 'a');
    const deleteCall = vi.fn();
    server.use(
      http.delete(`${PHOTOS_URL}/a`, () => {
        deleteCall();
        return new HttpResponse(null, { status: 204 });
      }),
    );

    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
    await user.click(screen.getByTestId('plant-photo-delete'));
    // Confirmation dialog appears; delete not yet called.
    expect(deleteCall).not.toHaveBeenCalled();
    const dialog = screen.getByTestId('confirm-dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Löschen' }));
    await waitFor(() => expect(deleteCall).toHaveBeenCalledTimes(1));
  });

  it('opens the lightbox with the large rendition on thumbnail click', async () => {
    const user = userEvent.setup();
    mockList([photo('a', true)], 'a');
    const requested = mockAttachmentBlobs();
    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
    await user.click(screen.getByTestId('plant-photo-thumb'));

    // The lightbox renders the image from an authenticated blob Object-URL and
    // loads the large (1280px) rendition (AC-02: originals stay out of the grid).
    const lightboxImg = (await screen.findByTestId('plant-photo-lightbox-image')) as HTMLImageElement;
    await waitFor(() => expect(lightboxImg.src).toMatch(/^blob:/));
    await waitFor(() =>
      expect(requested.some((p) => p.includes('/thumbnails/1280'))).toBe(true),
    );
  });

  it('hides all write actions for a viewer (AC-13)', async () => {
    mockList([photo('a', true)], 'a');
    renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('viewer'),
    });

    await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
    expect(screen.queryByTestId('plant-photo-add-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plant-photo-delete')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plant-photo-set-cover')).not.toBeInTheDocument();
    // But the viewer can still open the lightbox.
    expect(screen.getByTestId('plant-photo-thumb')).toBeInTheDocument();
  });
});
