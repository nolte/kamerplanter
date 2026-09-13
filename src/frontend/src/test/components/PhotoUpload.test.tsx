import { useState } from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';
import PhotoUpload from '@/components/common/PhotoUpload';

/**
 * PhotoUpload — the task-completion photo control (REQ-006).
 *
 * Until #1339 this posted to `POST /tasks/{key}/photos`, which no backend route
 * served: every upload answered 404, and a task with `requires_photo` could
 * therefore never be completed. The route exists now, on the NFR-013 attachment
 * fundament, so two things are asserted here that a `{ url }`-shaped static file
 * did not need:
 *
 * - the component carries the returned **`attachment_id`** into `photo_refs`,
 *   not the `uri`: NFR-013 §2.2 / AC-09 define every `photo_refs` list as a list
 *   of attachment ids, the shipped `migrate_photo_refs` job rewrites the URI
 *   shape *back* to ids, and a stored URI bakes in a tenant slug that a rename
 *   re-derives — which would break every task photo permanently;
 * - the preview renders through `AuthImage`, because the attachment URI is
 *   permission-gated and a native `<img src>` cannot send the Bearer header.
 */

const TENANT = 'test-tenant';
const ATTACHMENT_URI = `/api/v1/t/${TENANT}/attachments/att-1`;

function attachment() {
  return {
    attachment_id: 'att-1',
    uri: ATTACHMENT_URI,
    thumbnail_uris: null,
    mime_type: 'image/jpeg',
    byte_size: 3,
    original_filename: 'p.jpg',
  };
}

function blobResponse() {
  return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
    headers: { 'Content-Type': 'image/jpeg' },
  });
}

/**
 * `photoRefs` fed back from `onChange`, as the real caller's form state does.
 *
 * Needed because a removal's behaviour depends on whether the id was uploaded in
 * this session, so a test has to be able to upload *and then* remove against the
 * same mounted component. Re-rendering by hand loses the Redux provider, and a
 * fixed prop cannot express "the list the user just changed".
 */
function Harness({
  initial,
  onChange,
}: {
  initial: string[];
  onChange?: (refs: string[]) => void;
}) {
  const [refs, setRefs] = useState<string[]>(initial);
  return (
    <PhotoUpload
      taskKey="tk1"
      photoRefs={refs}
      onChange={(next) => {
        setRefs(next);
        onChange?.(next);
      }}
    />
  );
}

describe('PhotoUpload (REQ-006 — task photo upload)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uploads to the task photo route and stores the bare attachment id', async () => {
    const user = userEvent.setup();
    let requestedUrl: string | null = null;
    server.use(
      http.post(`/api/v1/t/:tenant/tasks/:key/photos`, ({ request }) => {
        requestedUrl = new URL(request.url).pathname;
        return HttpResponse.json(attachment());
      }),
    );
    const onChange = vi.fn();

    renderWithProviders(<PhotoUpload taskKey="tk1" photoRefs={[]} onChange={onChange} />);

    const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
    await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));

    await waitFor(() => expect(onChange).toHaveBeenCalled());
    // The id, not the URI: `photo_refs` is a list of attachment ids (NFR-013
    // §2.2 / AC-09). Asserting the exact value is what makes this red against a
    // component that stored `result.uri`.
    expect(onChange).toHaveBeenCalledWith(['att-1']);
    expect(onChange.mock.calls[0][0][0]).not.toContain('/attachments/');
    expect(requestedUrl).toBe(`/api/v1/t/${TENANT}/tasks/tk1/photos`);
  });

  it('renders a stored id by building the attachment URI at render time', async () => {
    // The stored ref is a bare id; the URI is rebuilt from the *current* slug,
    // which is exactly what survives a tenant rename.
    let fetched: string | null = null;
    server.use(
      http.get(ATTACHMENT_URI, ({ request }) => {
        fetched = new URL(request.url).pathname;
        return blobResponse();
      }),
    );

    renderWithProviders(
      <PhotoUpload taskKey="tk1" photoRefs={['att-1']} onChange={vi.fn()} />,
    );

    const img = (await screen.findByTestId('photo-preview-0')) as HTMLImageElement;
    // A blob Object-URL, never the permission-gated URI in `src`.
    expect(img.src).toMatch(/^blob:/);
    expect(img.src).not.toContain('/attachments/');
    await waitFor(() => expect(fetched).toBe(ATTACHMENT_URI));
  });

  it('keeps the dialog usable and reports nothing when the upload fails', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`/api/v1/t/:tenant/tasks/:key/photos`, () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'INTERNAL_ERROR',
            message: 'boom',
            details: [],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 500 },
        ),
      ),
    );
    const onChange = vi.fn();

    renderWithProviders(<PhotoUpload taskKey="tk1" photoRefs={[]} onChange={onChange} />);

    const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
    await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));

    // A failed upload must not push a ref the server never accepted.
    await waitFor(() => expect(screen.getByTestId('photo-upload')).toBeInTheDocument());
    expect(onChange).not.toHaveBeenCalled();
  });

  /**
   * Removing a photo (#1393).
   *
   * Before this, removal filtered the local array and issued no request — there was
   * no route to issue one to — so the stored object stayed, counting against the
   * tenant's quota with no surface that reached it for the `task` category.
   *
   * Deleting unconditionally was the over-correction, and it broke two things that
   * matter more than the leak:
   *
   * - a reopened task's completion photos are seeded into `photoRefs` from the
   *   persisted `task.photo_refs`, so one click destroyed documentation;
   * - hiding the control from growers (who may not `DELETE`) took away their only
   *   way to drop a wrong photo before submitting it — so the wrong photo got
   *   submitted instead.
   *
   * The contract is therefore: **de-stage always, destroy only what this session
   * uploaded, and only for a caller allowed to.** Everything a grower de-stages
   * becomes unreferenced and is collected by the nightly orphan sweep.
   */
  describe('removing a photo', () => {
    async function uploadOne(user: ReturnType<typeof userEvent.setup>) {
      server.use(
        http.post('/api/v1/t/:tenant/tasks/:key/photos', () => HttpResponse.json(attachment())),
      );
      const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
      await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));
    }

    it('destroys a photo this session uploaded, before dropping it from the list', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      let deleted: string | null = null;
      server.use(
        http.delete('/api/v1/t/:slug/tasks/tk1/photos/:id', ({ params }) => {
          deleted = params.id as string;
          return new HttpResponse(null, { status: 204 });
        }),
      );
      const onChange = vi.fn();

      // Rendered empty and uploaded here, so the id is *staged* rather than one
      // the task already carries — which is the whole distinction under test.
      renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
        store: createStoreWithTenantRole('lead'),
      });
      await uploadOne(user);
      await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));

      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(deleted).toBe('att-1'));
      expect(onChange).toHaveBeenLastCalledWith([]);
    });

    it('never destroys a photo the task already carried', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      let deleteAttempted = false;
      server.use(
        http.delete('/api/v1/t/:slug/tasks/tk1/photos/:id', () => {
          deleteAttempted = true;
          return new HttpResponse(null, { status: 204 });
        }),
      );
      const onChange = vi.fn();

      // Seeded from persisted `task.photo_refs`, the way `TaskDetailPage` does it
      // for a reopened task: these are the completion record, not staging.
      renderWithProviders(
        <PhotoUpload taskKey="tk1" photoRefs={['att-1']} onChange={onChange} />,
        { store: createStoreWithTenantRole('lead') },
      );

      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(onChange).toHaveBeenCalledWith([]));
      expect(deleteAttempted).toBe(false);
    });

    it('lets a grower de-stage, leaving the orphan to the nightly sweep', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      let deleteAttempted = false;
      server.use(
        http.delete('/api/v1/t/:slug/tasks/tk1/photos/:id', () => {
          deleteAttempted = true;
          return new HttpResponse(null, { status: 204 });
        }),
      );
      const onChange = vi.fn();

      renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
        store: createStoreWithTenantRole('grower'),
      });
      await uploadOne(user);
      await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));

      // The control is there for them — taking it away meant the wrong photo got
      // submitted, which is worse than the orphan the sweep collects.
      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(onChange).toHaveBeenLastCalledWith([]));
      // A grower may not DELETE an attachment (REQ-024 §1a.1), so none is attempted.
      expect(deleteAttempted).toBe(false);
    });

    it('keeps the photo in the list when the delete fails', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      server.use(
        http.delete('/api/v1/t/:slug/tasks/tk1/photos/:id', () =>
          HttpResponse.json({ message: 'boom' }, { status: 500 }),
        ),
      );
      const onChange = vi.fn();

      renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
        store: createStoreWithTenantRole('lead'),
      });
      await uploadOne(user);
      await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));
      onChange.mockClear();

      await user.click(await screen.findByTestId('photo-remove-0'));

      // Removing only after the request succeeds: an optimistic drop would tell the
      // user a photo is gone while it is still stored and still counted.
      await waitFor(() => expect(screen.getByTestId('photo-remove-0')).toBeInTheDocument());
      expect(onChange).not.toHaveBeenCalled();
    });
  });
});
