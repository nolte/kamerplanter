import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import AuthImage from '@/components/common/AuthImage';

const TENANT = 'test-tenant';
const URI = `/api/v1/t/${TENANT}/attachments/abc/thumbnails/512`;

/** Tiny valid blob body for the mocked attachment response. */
function blobResponse() {
  return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
    headers: { 'Content-Type': 'image/jpeg' },
  });
}

describe('AuthImage (REQ-034 — authenticated attachment rendering)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches the attachment via the authenticated axios client and renders a blob Object-URL', async () => {
    let requestedUrl: string | null = null;
    server.use(
      http.get(URI, ({ request }) => {
        requestedUrl = new URL(request.url).pathname;
        return blobResponse();
      }),
    );

    renderWithProviders(<AuthImage uri={URI} alt="Plant photo" data-testid="auth-image" />);

    // The image is rendered from a blob Object-URL, NOT the raw permission-gated
    // attachment URI (a native <img src={uri}> could not send the Bearer header).
    const img = (await screen.findByTestId('auth-image')) as HTMLImageElement;
    expect(img.src).toMatch(/^blob:/);
    expect(img.src).not.toContain('/attachments/');
    expect(img).toHaveAttribute('alt', 'Plant photo');

    // The fetch went through the axios client to the full tenant-scoped path
    // (the plain client's /api/v1 baseURL + the de-prefixed /t/{slug}/... path),
    // exactly once — proving the request was made, not skipped.
    expect(requestedUrl).toBe(URI);
  });

  it('shows a skeleton placeholder while the blob is loading', async () => {
    server.use(http.get(URI, async () => blobResponse()));

    renderWithProviders(<AuthImage uri={URI} alt="Plant photo" data-testid="auth-image" />);

    // Before the request resolves, the loading box (suffixed test id) is present.
    expect(screen.getByTestId('auth-image-loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('auth-image')).toBeInTheDocument());
  });

  it('renders a neutral error box (never a broken image) when the fetch fails', async () => {
    const onError = vi.fn();
    server.use(http.get(URI, () => new HttpResponse(null, { status: 403 })));

    renderWithProviders(
      <AuthImage uri={URI} alt="Plant photo" data-testid="auth-image" onError={onError} />,
    );

    await waitFor(() => expect(screen.getByTestId('auth-image-error')).toBeInTheDocument());
    // No broken <img> is rendered; the error box carries an accessible label.
    expect(screen.queryByTestId('auth-image')).not.toBeInTheDocument();
    expect(screen.getByTestId('auth-image-error')).toHaveAttribute('role', 'img');
    expect(onError).toHaveBeenCalled();
  });
});
