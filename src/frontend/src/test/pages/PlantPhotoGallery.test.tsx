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
const SPECIES_KEY = 'sp-basil';
const PHOTOS_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/photos`;
// Reference images are a global (non-tenant-scoped) species resource.
const REFERENCE_URL = `/api/v1/species/${SPECIES_KEY}/reference-images`;

/** Registers a reference-image response and records how often it was requested. */
function mockReferenceImages(
  images: { source_url: string; license?: string | null; attribution?: string | null; organ?: string | null; source?: string | null }[],
): { calls: () => number } {
  let count = 0;
  server.use(
    http.get(REFERENCE_URL, () => {
      count += 1;
      return HttpResponse.json({ species_key: SPECIES_KEY, count: images.length, images });
    }),
  );
  return { calls: () => count };
}
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

type AssessmentOverride = {
  rating: 'good' | 'fair' | 'poor';
  adapter?: string;
  is_plant?: boolean;
  expected_species_matched?: boolean | null;
  suggestions?: { scientific_name: string; confidence: number; external_id: string | null }[];
};

function photo(
  id: string,
  isCover = false,
  overrides: {
    caption?: string | null;
    taken_on?: string | null;
    quality_assessment?: AssessmentOverride | null;
  } = {},
) {
  const uri = `/api/v1/t/${TENANT}/attachments/${id}`;
  const qa = overrides.quality_assessment
    ? {
        adapter: overrides.quality_assessment.adapter ?? 'plantnet',
        assessed_at: '2026-06-19T11:00:00Z',
        is_plant: overrides.quality_assessment.is_plant ?? true,
        rating: overrides.quality_assessment.rating,
        expected_species_matched:
          overrides.quality_assessment.expected_species_matched ?? null,
        suggestions: overrides.quality_assessment.suggestions ?? [],
      }
    : null;
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
    caption: overrides.caption ?? null,
    taken_on: overrides.taken_on ?? null,
    quality_assessment: qa,
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
    // The blob render path is multi-step (MSW -> axios blob -> createObjectURL ->
    // setState); under the CI runner's constrained parallelism it can exceed the
    // 1s default waitFor budget, so these image assertions get explicit headroom
    // (mirrors the rationale for the 30s testTimeout in vitest.config.ts).
    const imgs = (await screen.findAllByTestId(
      'plant-photo-image',
      undefined,
      { timeout: 10000 },
    )) as HTMLImageElement[];
    await waitFor(() => expect(imgs[0].src).toMatch(/^blob:/), { timeout: 10000 });
    imgs.forEach((img) => expect(img.src).not.toContain('/attachments/'));

    // AC-02: the grid loads the medium (512px) rendition only — never the
    // original or the large (1280px) rendition.
    await waitFor(() => expect(requested.length).toBeGreaterThan(0), { timeout: 10000 });
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
    const lightboxImg = (await screen.findByTestId(
      'plant-photo-lightbox-image',
      undefined,
      { timeout: 10000 },
    )) as HTMLImageElement;
    await waitFor(() => expect(lightboxImg.src).toMatch(/^blob:/), { timeout: 10000 });
    await waitFor(
      () => expect(requested.some((p) => p.includes('/thumbnails/1280'))).toBe(true),
      { timeout: 10000 },
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
    // The edit action is also hidden for viewers (read-only).
    expect(screen.queryByTestId('plant-photo-edit')).not.toBeInTheDocument();
    // But the viewer can still open the lightbox.
    expect(screen.getByTestId('plant-photo-thumb')).toBeInTheDocument();
  });

  describe('photo metadata (REQ-034 §2.1 v1.2)', () => {
    it('renders the capture date and a truncated caption under the thumbnail', async () => {
      // taken_on overrides created_at for the displayed date.
      mockList([photo('a', true, { caption: 'My favourite basil', taken_on: '2026-05-10' })], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      expect(screen.getByTestId('plant-photo-caption')).toHaveTextContent('My favourite basil');
      // The date is the locale-formatted taken_on (2026-05-10), not the upload date.
      const dateText = screen.getByTestId('plant-photo-date').textContent ?? '';
      expect(dateText).toMatch(/2026/);
      expect(dateText).toMatch(/05|5/);
    });

    it('falls back to the upload date when taken_on is null', async () => {
      mockList([photo('a', true, { taken_on: null })], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      // created_at is 2026-06-19 → display falls back to it.
      expect(screen.getByTestId('plant-photo-date').textContent ?? '').toMatch(/2026/);
      // No caption → no caption node rendered.
      expect(screen.queryByTestId('plant-photo-caption')).not.toBeInTheDocument();
    });

    it('opens the edit dialog and saves caption + date via PATCH', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      const patchBody = vi.fn();
      server.use(
        http.patch(`${PHOTOS_URL}/a`, async ({ request }) => {
          patchBody(await request.json());
          return HttpResponse.json(photo('a', true, { caption: 'Updated', taken_on: '2026-05-01' }));
        }),
      );

      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-edit'));

      const captionInput = await screen.findByTestId('plant-photo-caption-input');
      await user.type(captionInput, 'Updated');
      const dateInput = screen.getByTestId('plant-photo-takenon-input');
      await user.clear(dateInput);
      await user.type(dateInput, '2026-05-01');

      await user.click(screen.getByTestId('plant-photo-edit-save'));

      await waitFor(() => expect(patchBody).toHaveBeenCalledTimes(1));
      expect(patchBody).toHaveBeenCalledWith(
        expect.objectContaining({ caption: 'Updated', taken_on: '2026-05-01' }),
      );
      // The dialog closes and the gallery reflects the new caption.
      await waitFor(() =>
        expect(screen.getByTestId('plant-photo-caption')).toHaveTextContent('Updated'),
      );
    });

    it('blocks saving and shows a counter error when the caption exceeds 500 chars', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      const patchCall = vi.fn();
      server.use(
        http.patch(`${PHOTOS_URL}/a`, () => {
          patchCall();
          return HttpResponse.json(photo('a', true));
        }),
      );

      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-edit'));

      const captionInput = await screen.findByTestId('plant-photo-caption-input');
      // Paste 501 chars (fireEvent-style fast input via paste).
      await user.click(captionInput);
      await user.paste('x'.repeat(501));

      // The save button is disabled (pointer-events:none) so no request fires.
      const saveBtn = screen.getByTestId('plant-photo-edit-save');
      expect(saveBtn).toBeDisabled();
      expect(patchCall).not.toHaveBeenCalled();
    });

    it('caps the date input at today so a future date cannot be entered', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-edit'));

      const dateInput = (await screen.findByTestId('plant-photo-takenon-input')) as HTMLInputElement;
      const today = new Date().toISOString().slice(0, 10);
      expect(dateInput.max).toBe(today);
    });

    it('does not render an edit action for a viewer', async () => {
      mockList([photo('a', true, { caption: 'visible to viewer' })], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('viewer'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      expect(screen.queryByTestId('plant-photo-edit')).not.toBeInTheDocument();
      // But the caption is still shown read-only.
      expect(screen.getByTestId('plant-photo-caption')).toHaveTextContent('visible to viewer');
    });
  });

  describe('quality assessment (REQ-034 §4a)', () => {
    const ADAPTERS_URL = `${PHOTOS_URL}/assess/adapters`;

    function mockAdapters(localAvailable = false) {
      server.use(
        http.get(ADAPTERS_URL, () =>
          HttpResponse.json({
            adapters: [
              { key: 'plantnet', available: true, external: true, requires_consent: true },
              {
                key: 'local_embedding',
                available: localAvailable,
                external: false,
                requires_consent: false,
              },
            ],
          }),
        ),
      );
    }

    it('renders a persisted quality badge on the thumbnail (visible afterwards)', async () => {
      mockList([photo('a', true, { quality_assessment: { rating: 'good' } })], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      expect(screen.getByTestId('plant-photo-quality-badge')).toBeInTheDocument();
      expect(screen.getByTestId('quality-badge-good')).toBeInTheDocument();
    });

    it('triggers an assessment and shows the Ampel verdict + suggestions', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      mockAdapters();
      const assessBody = vi.fn();
      server.use(
        http.post(`${PHOTOS_URL}/a/assess`, async ({ request }) => {
          assessBody(await request.json());
          return HttpResponse.json(
            photo('a', true, {
              quality_assessment: {
                rating: 'good',
                expected_species_matched: true,
                suggestions: [
                  { scientific_name: 'Ocimum basilicum', confidence: 0.95, external_id: 'plantnet:0' },
                ],
              },
            }),
          );
        }),
      );

      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-assess'));

      // Dialog opens and loads the adapters.
      await screen.findByTestId('plant-photo-assess-dialog');
      const runBtn = await screen.findByTestId('assess-run');
      await user.click(runBtn);

      await waitFor(() => expect(assessBody).toHaveBeenCalledTimes(1));
      expect(assessBody).toHaveBeenCalledWith(expect.objectContaining({ adapter: 'plantnet' }));

      // The Ampel verdict + the top suggestion appear in the result block.
      const result = await screen.findByTestId('assess-result');
      expect(within(result).getByText('Ocimum basilicum')).toBeInTheDocument();
      expect(within(result).getByTestId('quality-badge-good')).toBeInTheDocument();

      // Persisted: closing the dialog leaves the badge on the thumbnail.
      await user.click(screen.getByTestId('assess-close'));
      await waitFor(() =>
        expect(screen.getByTestId('plant-photo-quality-badge')).toBeInTheDocument(),
      );
    });

    it('shows a privacy notice for the external Pl@ntNet path', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      mockAdapters();
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-assess'));
      // Pl@ntNet is the default selection → the external notice is shown.
      expect(await screen.findByTestId('assess-external-notice')).toBeInTheDocument();
    });

    it('disables the DINOv2 option when it is not available (no dead code)', async () => {
      const user = userEvent.setup();
      mockList([photo('a', true)], 'a');
      mockAdapters(false);
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      await user.click(screen.getByTestId('plant-photo-assess'));

      // The DINOv2 radio is rendered but disabled (greyed-out with a hint).
      const localRadio = (await screen.findByTestId('assess-adapter-local_embedding')).querySelector(
        'input',
      ) as HTMLInputElement;
      expect(localRadio).toBeDisabled();
      // Pl@ntNet stays enabled.
      const plantnetRadio = screen
        .getByTestId('assess-adapter-plantnet')
        .querySelector('input') as HTMLInputElement;
      expect(plantnetRadio).not.toBeDisabled();
    });

    it('does not offer the assess action to a viewer but shows a persisted badge', async () => {
      mockList([photo('a', true, { quality_assessment: { rating: 'fair' } })], 'a');
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('viewer'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      // Viewer cannot trigger a new assessment...
      expect(screen.queryByTestId('plant-photo-assess')).not.toBeInTheDocument();
      // ...but sees the persisted verdict.
      expect(screen.getByTestId('quality-badge-fair')).toBeInTheDocument();
    });
  });

  describe('species reference images (REQ-029-A)', () => {
    const refImage = (overrides: Partial<{ source_url: string; license: string | null; attribution: string | null; organ: string | null }> = {}) => ({
      source_url: overrides.source_url ?? 'https://example.org/leaf.jpg',
      license: overrides.license ?? 'CC-BY',
      attribution: overrides.attribution ?? 'Jane Doe',
      organ: overrides.organ ?? 'leaf',
      source: 'gbif',
    });

    it('renders the own-photos and reference-images sections separately when references exist', async () => {
      mockList([photo('a', true)], 'a');
      mockReferenceImages([
        refImage({ source_url: 'https://example.org/leaf.jpg' }),
        refImage({ source_url: 'https://example.org/flower.jpg', organ: 'flower', license: 'CC0', attribution: null }),
      ]);
      renderWithProviders(
        <PlantPhotoGallery plantInstanceKey={PLANT_KEY} speciesKey={SPECIES_KEY} scientificName="Ocimum basilicum" />,
        { store: storeWithRole('grower') },
      );

      // Own photos section header is present with the user's own photo grid.
      await waitFor(() => expect(screen.getByTestId('own-photos-section-title')).toBeInTheDocument());
      expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument();

      // The clearly separated reference-images section appears with its own header.
      const refSection = await screen.findByTestId('reference-images-section');
      expect(within(refSection).getByTestId('reference-images-section-title')).toBeInTheDocument();
      expect(within(refSection).getAllByTestId('reference-image-item')).toHaveLength(2);
      // Legally required CC-BY attribution caption is rendered.
      expect(within(refSection).getByText('© Jane Doe · CC-BY')).toBeInTheDocument();
    });

    it('hides the reference-images section when the list is empty', async () => {
      mockList([photo('a', true)], 'a');
      mockReferenceImages([]);
      renderWithProviders(
        <PlantPhotoGallery plantInstanceKey={PLANT_KEY} speciesKey={SPECIES_KEY} scientificName="Ocimum basilicum" />,
        { store: storeWithRole('grower') },
      );

      await waitFor(() => expect(screen.getByTestId('own-photos-section-title')).toBeInTheDocument());
      // Give the async reference fetch a chance to resolve, then assert it stays hidden.
      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      expect(screen.queryByTestId('reference-images-section')).not.toBeInTheDocument();
    });

    it('does not request reference images when the instance has no species_key', async () => {
      mockList([photo('a', true)], 'a');
      const ref = mockReferenceImages([refImage()]);
      renderWithProviders(<PlantPhotoGallery plantInstanceKey={PLANT_KEY} />, {
        store: storeWithRole('grower'),
      });

      await waitFor(() => expect(screen.getByTestId('plant-photo-item')).toBeInTheDocument());
      // No species → no reference section and, crucially, no API call.
      expect(screen.queryByTestId('reference-images-section')).not.toBeInTheDocument();
      expect(ref.calls()).toBe(0);
    });

    it('requests reference images exactly once when a species_key is provided', async () => {
      mockList([photo('a', true)], 'a');
      const ref = mockReferenceImages([refImage()]);
      renderWithProviders(
        <PlantPhotoGallery plantInstanceKey={PLANT_KEY} speciesKey={SPECIES_KEY} />,
        { store: storeWithRole('grower') },
      );

      await waitFor(() => expect(screen.getByTestId('reference-images-section')).toBeInTheDocument());
      expect(ref.calls()).toBe(1);
    });
  });
});
