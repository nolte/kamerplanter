import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import DiaryPhotoStrip from '@/components/diary/DiaryPhotoStrip';

/**
 * REQ-051 §6.1 — a diary entry's photos as 512-px previews with a lightbox.
 *
 * The rendition assertion is the point of this file: the grid must never pull
 * the original or the 1280-px rendition, or a list of entries with five photos
 * each would download megabytes to show thumbnails.
 */

const TENANT = 'test-tenant';

/** Serve any attachment rendition and record which paths were requested. */
function mockAttachmentBlobs(): string[] {
  const requested: string[] = [];
  server.use(
    http.get(`/api/v1/t/${TENANT}/attachments/:id/thumbnails/:px`, ({ request }) => {
      requested.push(new URL(request.url).pathname);
      return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
        headers: { 'Content-Type': 'image/jpeg' },
      });
    }),
    http.get(`/api/v1/t/${TENANT}/attachments/:id`, ({ request }) => {
      requested.push(new URL(request.url).pathname);
      return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
        headers: { 'Content-Type': 'image/jpeg' },
      });
    }),
  );
  return requested;
}

describe('DiaryPhotoStrip (REQ-051 §6.1)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders nothing for an entry without photos', () => {
    renderWithProviders(<DiaryPhotoStrip photoRefs={[]} />);
    expect(screen.queryByTestId('diary-photo-strip')).not.toBeInTheDocument();
  });

  it('loads the 512-px rendition for the previews, never the original', async () => {
    const requested = mockAttachmentBlobs();
    renderWithProviders(<DiaryPhotoStrip photoRefs={['a1', 'a2']} />);

    expect(screen.getAllByTestId('diary-photo-thumb')).toHaveLength(2);
    await waitFor(() => expect(requested.length).toBeGreaterThanOrEqual(2), { timeout: 10000 });
    expect(requested.every((p) => p.includes('/thumbnails/512'))).toBe(true);
    expect(requested.some((p) => p.includes('/thumbnails/1280'))).toBe(false);
    expect(requested.some((p) => /\/attachments\/[^/]+$/.test(p))).toBe(false);
  });

  it('opens the lightbox on click and pages through the photos', async () => {
    const user = userEvent.setup();
    const requested = mockAttachmentBlobs();
    renderWithProviders(<DiaryPhotoStrip photoRefs={['a1', 'a2']} />);

    await user.click(screen.getAllByTestId('diary-photo-thumb')[0]);
    expect(await screen.findByTestId('diary-photo-lightbox')).toBeInTheDocument();

    // Only the full view pulls the 1280-px rendition (§4.4's rule, applied to
    // the web UI: previews stay small, the opened photo may be larger).
    await waitFor(() => expect(requested.some((p) => p.includes('/thumbnails/1280'))).toBe(true), {
      timeout: 10000,
    });

    // First photo: no "previous", but a "next".
    expect(screen.getByTestId('diary-photo-lightbox-prev')).toBeDisabled();
    await user.click(screen.getByTestId('diary-photo-lightbox-next'));
    expect(screen.getByTestId('diary-photo-lightbox-next')).toBeDisabled();
    expect(screen.getByTestId('diary-photo-lightbox-prev')).toBeEnabled();

    await user.click(screen.getByTestId('diary-photo-lightbox-dismiss'));
    await waitFor(() =>
      expect(screen.queryByTestId('diary-photo-lightbox')).not.toBeInTheDocument(),
    );
  });
});
