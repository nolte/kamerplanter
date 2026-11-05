/**
 * The photo gallery of a bed (REQ-053 GP-FR-051, WP 8.19): the list newest first with the cover, the empty and
 * error states, upload then link, choosing and clearing the cover, remove only where the server allows it, the
 * limit of 50 photos and the axe pass.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedPhotosTab from './BedPhotosTab';
import type { BedPhoto, BedPhotoGallery } from './bedPhotoApi';

// The capture panel relies on canvas/getUserMedia (not in jsdom): a button that hands a file to the dialog.
vi.mock('@/components/identification/ImageCapturePanel', () => ({
  default: ({ onImageReady }: { onImageReady: (file: File, url: string) => void }) => (
    <button
      type="button"
      data-testid="mock-pick-image"
      onClick={() => onImageReady(new File([new Uint8Array([1, 2, 3])], 'bed.jpg', { type: 'image/jpeg' }), 'blob:preview')}
    >
      pick
    </button>
  ),
}));

const BASE = '/api/v1/t/:tenant';
const BED = 'loc_b03';

function photo(id: string, overrides: Partial<BedPhoto> = {}): BedPhoto {
  const uri = `/api/v1/t/test-tenant/attachments/${id}`;
  return {
    attachment_id: id,
    uri,
    thumbnail_uris: { small: `${uri}/thumbnails/128`, medium: `${uri}/thumbnails/512`, large: `${uri}/thumbnails/1280` },
    mime_type: 'image/jpeg',
    created_at: '2026-06-14T10:00:00Z',
    is_cover: false,
    can_remove: true,
    ...overrides,
  };
}

function gallery(photos: BedPhoto[]): BedPhotoGallery {
  return {
    location_key: BED,
    cover_photo_ref: photos.find((item) => item.is_cover)?.attachment_id ?? null,
    photos,
    max_photos: 50,
  };
}

/**
 * A text field of a multipart body. Not `request.formData()`: under this Node/undici build the parser asserts on
 * the `file` part and throws inside the handler (see `PlantDiaryTab.test.tsx`).
 */
function multipartField(body: string, name: string): string | null {
  const match = new RegExp(`name="${name}"(?:;[^\\r\\n]*)?\\r?\\n(?:[^\\r\\n]+\\r?\\n)*\\r?\\n([^\\r\\n]*)`).exec(body);
  return match ? match[1] : null;
}

function apiError(status: number, code: string) {
  return HttpResponse.json(
    { error_id: 'err_1', error_code: code, message: code, details: [], timestamp: '', path: '', method: 'POST' },
    { status },
  );
}

/** Answers the gallery with `initial`; every write answers with what `next` returns and is recorded. */
function useBackend(initial: BedPhoto[]) {
  const requests: { method: string; path: string; body: unknown }[] = [];
  let current = gallery(initial);
  server.use(
    http.get(`${BASE}/attachments/:id/thumbnails/:px`, () =>
      HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, { headers: { 'Content-Type': 'image/jpeg' } }),
    ),
    http.get(`${BASE}/locations/:key/photos`, () => HttpResponse.json(current)),
    http.post(`${BASE}/attachments`, async ({ request }) => {
      requests.push({ method: 'POST', path: 'attachments', body: { category: multipartField(await request.text(), 'category') } });
      return HttpResponse.json({ attachment_id: 'p_new' }, { status: 201 });
    }),
    http.post(`${BASE}/locations/:key/photos`, async ({ request }) => {
      const body = (await request.json()) as { attachment_id: string };
      requests.push({ method: 'POST', path: 'photos', body });
      const first = current.photos.length === 0;
      current = gallery([photo(body.attachment_id, { is_cover: first }), ...current.photos]);
      return HttpResponse.json(current, { status: 201 });
    }),
    http.put(`${BASE}/locations/:key/photos/cover`, async ({ request }) => {
      const body = (await request.json()) as { attachment_id: string | null };
      requests.push({ method: 'PUT', path: 'cover', body });
      current = gallery(current.photos.map((item) => ({ ...item, is_cover: item.attachment_id === body.attachment_id })));
      return HttpResponse.json(current);
    }),
    http.delete(`${BASE}/locations/:key/photos/:id`, ({ params }) => {
      requests.push({ method: 'DELETE', path: `photos/${String(params.id)}`, body: null });
      current = gallery(current.photos.filter((item) => item.attachment_id !== params.id));
      return HttpResponse.json(current);
    }),
  );
  return requests;
}

function renderTab({
  role = 'grower',
  coverPhotoRef = null,
  onCoverChange = () => undefined,
}: { role?: 'viewer' | 'grower' | 'lead'; coverPhotoRef?: string | null; onCoverChange?: () => void } = {}) {
  return renderWithProviders(
    <BedPhotosTab
      bedKey={BED}
      bedName="Raised bed 3"
      coverPhotoRef={coverPhotoRef}
      canEdit={role !== 'viewer'}
      onCoverChange={onCoverChange}
    />,
    { store: createTestStore({ ...tenantState(role), ...authState() }) },
  );
}

afterEach(() => cleanup());

describe('BedPhotosTab (GP-FR-051)', () => {
  it('lists the photos newest first, marks the cover and counts against the limit', async () => {
    useBackend([photo('p2', { is_cover: true, created_at: '2026-06-20T10:00:00Z' }), photo('p1')]);
    const view = renderTab({ coverPhotoRef: 'p2' });
    const list = await screen.findByRole('list', { name: 'Photos of Raised bed 3' });
    const items = within(list).getAllByRole('listitem');
    expect(items.map((item) => item.dataset.testid)).toEqual(['bed-photo-p2', 'bed-photo-p1']);
    expect(within(items[0]).getByTestId('bed-photo-cover-p2')).toHaveTextContent('Cover');
    expect(within(items[1]).queryByTestId('bed-photo-cover-p1')).not.toBeInTheDocument();
    expect(screen.getByTestId('bed-photos-count')).toHaveTextContent('2 of at most 50 photos');
    await expectNoA11yViolations(view.container);
  });

  it('explains the empty gallery and offers the first upload to a grower', async () => {
    useBackend([]);
    const view = renderTab();
    expect(await screen.findByText('No photos of the bed yet')).toBeInTheDocument();
    expect(screen.getByText(/The first photo becomes the cover automatically/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add the first photo' })).toBeInTheDocument();
    await expectNoA11yViolations(view.container);
  });

  it('shows a viewer the photos without add, cover or remove controls', async () => {
    useBackend([photo('p1', { is_cover: true, can_remove: false })]);
    renderTab({ role: 'viewer', coverPhotoRef: 'p1' });
    await screen.findByTestId('bed-photo-p1');
    expect(screen.queryByTestId('bed-photos-add')).not.toBeInTheDocument();
    expect(screen.queryByTestId('bed-photo-toggle-cover-p1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('bed-photo-remove-p1')).not.toBeInTheDocument();
  });

  it('says so when the gallery cannot be read and loads it again on retry', async () => {
    let fail = true;
    useBackend([photo('p1')]);
    server.use(
      http.get(`${BASE}/locations/:key/photos`, () =>
        fail ? HttpResponse.json({ detail: 'Internal error' }, { status: 500 }) : HttpResponse.json(gallery([photo('p1')])),
      ),
    );
    const user = userEvent.setup();
    renderTab();
    expect(await screen.findByText(/could not be loaded/)).toBeInTheDocument();
    fail = false;
    await user.click(screen.getByRole('button', { name: /retry|try again/i }));
    expect(await screen.findByTestId('bed-photo-p1')).toBeInTheDocument();
  });

  it('uploads a photo as category location, links it to the bed and reloads the head for the new cover', async () => {
    const requests = useBackend([]);
    const onCoverChange = vi.fn();
    const user = userEvent.setup();
    renderTab({ onCoverChange });
    await user.click(await screen.findByTestId('bed-photos-add'));
    const dialog = await screen.findByTestId('plant-photo-upload-dialog');
    expect(within(dialog).getByText('Add a photo to Raised bed 3')).toBeInTheDocument();
    await user.click(within(dialog).getByTestId('mock-pick-image'));
    await user.click(within(dialog).getByTestId('plant-photo-upload-confirm'));
    expect(await screen.findByTestId('bed-photo-p_new')).toBeInTheDocument();
    expect(requests).toEqual([
      { method: 'POST', path: 'attachments', body: { category: 'location' } },
      { method: 'POST', path: 'photos', body: { attachment_id: 'p_new' } },
    ]);
    expect(screen.getByTestId('bed-photo-cover-p_new')).toBeInTheDocument();
    expect(onCoverChange).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByTestId('plant-photo-upload-dialog')).not.toBeInTheDocument());
  });

  it('sets another photo as cover and clears the cover, each through PUT .../photos/cover', async () => {
    const requests = useBackend([photo('p2', { is_cover: true }), photo('p1')]);
    const onCoverChange = vi.fn();
    const user = userEvent.setup();
    renderTab({ coverPhotoRef: 'p2', onCoverChange });
    const setCover = await screen.findByTestId('bed-photo-toggle-cover-p1');
    expect(setCover).toHaveAccessibleName('Cover photo');
    expect(setCover).toHaveAttribute('aria-pressed', 'false');
    await user.click(setCover);
    expect(await screen.findByTestId('bed-photo-cover-p1')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-photo-cover-p2')).not.toBeInTheDocument();

    const clear = screen.getByTestId('bed-photo-toggle-cover-p1');
    expect(clear).toHaveAccessibleName('Cover photo');
    expect(clear).toHaveAttribute('aria-pressed', 'true');
    await user.click(clear);
    await waitFor(() => expect(screen.queryByTestId('bed-photo-cover-p1')).not.toBeInTheDocument());
    expect(requests.map((request) => request.body)).toEqual([{ attachment_id: 'p1' }, { attachment_id: null }]);
    expect(onCoverChange).toHaveBeenCalledTimes(2);
  });

  it('offers remove only where can_remove is set and removes after the confirmation', async () => {
    const requests = useBackend([photo('p2', { can_remove: false }), photo('p1', { can_remove: true })]);
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('bed-photo-p2');
    expect(screen.queryByTestId('bed-photo-remove-p2')).not.toBeInTheDocument();

    await user.click(screen.getByTestId('bed-photo-remove-p1'));
    const dialog = await screen.findByRole('alertdialog', { name: 'Remove the photo from the bed?' });
    await user.click(within(dialog).getByTestId('confirm-dialog-cancel'));
    expect(requests).toEqual([]);

    await user.click(screen.getByTestId('bed-photo-remove-p1'));
    const again = await screen.findByRole('alertdialog', { name: 'Remove the photo from the bed?' });
    await user.click(within(again).getByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(screen.queryByTestId('bed-photo-p1')).not.toBeInTheDocument());
    expect(requests).toEqual([{ method: 'DELETE', path: 'photos/p1', body: null }]);
    expect(screen.getByTestId('bed-photo-p2')).toBeInTheDocument();
  });

  it('locks the upload at 50 photos and says why', async () => {
    useBackend(Array.from({ length: 50 }, (_, index) => photo(`p${index}`)));
    renderTab();
    expect(await screen.findByTestId('bed-photos-limit')).toHaveTextContent('maximum of 50 photos');
    expect(screen.getByTestId('bed-photos-add')).toBeDisabled();
  });

  it('names the limit in the dialog when the link is refused with location.photo_limit_reached', async () => {
    useBackend([]);
    server.use(http.post(`${BASE}/locations/:key/photos`, () => apiError(422, 'location.photo_limit_reached')));
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('bed-photos-add'));
    const dialog = await screen.findByTestId('plant-photo-upload-dialog');
    await user.click(within(dialog).getByTestId('mock-pick-image'));
    await user.click(within(dialog).getByTestId('plant-photo-upload-confirm'));
    expect(await within(dialog).findByTestId('plant-photo-upload-error')).toHaveTextContent('maximum of 50 photos');
  });
});
