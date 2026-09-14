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

function attachment(attachmentId = 'att-1') {
  return {
    attachment_id: attachmentId,
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
  // `initial` is what the task carried at load, exactly as `TaskDetailPage` seeds
  // both lists from `task.photo_refs`. Passing it as `persistedRefs` is what makes
  // "staged" survive a remount — the tab switch that used to lose it.
  return (
    <PhotoUpload
      taskKey="tk1"
      photoRefs={refs}
      persistedRefs={initial}
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

    it('offers no remove control at all for a photo the task already carried', async () => {
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));

      // Seeded from persisted `task.photo_refs`, the way `TaskDetailPage` does it
      // for a reopened task: these are the completion record, not staging.
      renderWithProviders(
        <PhotoUpload
          taskKey="tk1"
          photoRefs={['att-1']}
          persistedRefs={['att-1']}
          onChange={vi.fn()}
        />,
        { store: createStoreWithTenantRole('lead') },
      );

      // The photo is shown — only the control is withheld.
      expect(await screen.findByTestId('photo-preview-0')).toBeInTheDocument();
      // Neither meaning of "remove" works here: destroying loses the record of a
      // completion, and de-staging is a silent no-op because `complete_task` merges
      // `photo_refs` append-only and never prunes — the photo would come back.
      expect(screen.queryByTestId('photo-remove-0')).toBeNull();
    });

    it('issues the delete for a grower too, instead of only de-staging', async () => {
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

      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(onChange).toHaveBeenLastCalledWith([]));
      // This assertion is the whole point and it used to read `toBe(false)`, with a
      // comment explaining that a grower may not DELETE an attachment and that the
      // nightly sweep would collect what they left behind. The sweep then shipped
      // disabled, so what the old behaviour actually produced was a stored object
      // nothing would ever reach — for the role that uploads most of these photos.
      //
      // The server now decides per photo rather than per role: a staged upload may
      // be withdrawn by whoever made it, the task's completion record stays
      // lead-only. So the request goes out, and a refusal comes back as a 404 that
      // de-stages without pretending the bytes are gone.
      expect(deleteAttempted).toBe(true);
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

  /**
   * sha256 deduplication (#1424 review round 3).
   *
   * `AttachmentService.upload` returns the **existing** attachment when the bytes
   * already exist in the tenant — across categories, not just within one. So an
   * upload can hand back an id the task already carries, and treating that as a
   * fresh staging put the destroy control back on a photo it had been withdrawn
   * from, and duplicated the id in the list.
   */
  describe('an upload that deduplicates to an existing attachment', () => {
    it('does not mark a photo the task already carries as staged', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      // Dedup: the upload answers with the id already in `photoRefs`.
      server.use(
        http.post('/api/v1/t/:tenant/tasks/:key/photos', () => HttpResponse.json(attachment())),
      );

      renderWithProviders(<Harness initial={['att-1']} />, {
        store: createStoreWithTenantRole('lead'),
      });
      await screen.findByTestId('photo-preview-0');
      const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
      await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));

      // Still no destroy control: the id was persisted before this upload, and an
      // upload that merely resolved to it does not make it staging.
      await waitFor(() => expect(screen.queryByTestId('photo-remove-0')).toBeNull());
    });

    it('does not add the id twice', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      server.use(
        http.post('/api/v1/t/:tenant/tasks/:key/photos', () => HttpResponse.json(attachment())),
      );
      const onChange = vi.fn();

      renderWithProviders(<Harness initial={['att-1']} onChange={onChange} />, {
        store: createStoreWithTenantRole('lead'),
      });
      await screen.findByTestId('photo-preview-0');
      const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
      await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));

      // A duplicate would give two previews with the same React key and submit the
      // id twice in `photo_refs`.
      await waitFor(() => expect(screen.queryByTestId('photo-preview-1')).toBeNull());
      for (const call of onChange.mock.calls) {
        expect(new Set(call[0]).size).toBe(call[0].length);
      }
    });
  });

  /**
   * A staged photo the server refuses to destroy (#1424 review round 3).
   *
   * Reachable through sha256 deduplication: staging a file whose bytes already exist
   * as a plant-gallery photo hands back *that* attachment, and the task route rightly
   * refuses to destroy a gallery photo. Before this the button stayed dead — the
   * error surfaced and the entry never left the list.
   */
  describe('when the server refuses to destroy a staged photo', () => {
    async function stageOne(user: ReturnType<typeof userEvent.setup>) {
      server.use(
        http.post('/api/v1/t/:tenant/tasks/:key/photos', () => HttpResponse.json(attachment())),
      );
      const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
      await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));
    }

    it('de-stages it on a 404 rather than leaving a dead control', async () => {
      const user = userEvent.setup();
      server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
      server.use(
        http.delete('/api/v1/t/:slug/tasks/tk1/photos/:id', () =>
          HttpResponse.json(
            { error_id: 'e1', error_code: 'NOT_FOUND', message: 'attachment not found' },
            { status: 404 },
          ),
        ),
      );
      const onChange = vi.fn();

      renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
        store: createStoreWithTenantRole('lead'),
      });
      await stageOne(user);
      await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));

      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(onChange).toHaveBeenLastCalledWith([]));
    });

    it('keeps it on any other failure, because it may still be there', async () => {
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
      await stageOne(user);
      await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));
      onChange.mockClear();

      await user.click(await screen.findByTestId('photo-remove-0'));

      await waitFor(() => expect(screen.getByTestId('photo-remove-0')).toBeInTheDocument());
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  /**
   * The completion form is conditionally rendered (`{tab === 1 && isActionable && …}`),
   * so this component unmounts on a tab switch while `photoRefs` lives on in the
   * page. Tracking "staged" in component state lost it on that remount, and the
   * staged photo then had no remove control at all — not merely undestroyable but
   * un-de-stageable, so it was submitted with the completion (#1424 round 4).
   */
  it('keeps the remove control after the component is unmounted and remounted', async () => {
    const user = userEvent.setup();
    server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/photos', () => HttpResponse.json(attachment())),
    );

    function TabSwitcher() {
      const [refs, setRefs] = useState<string[]>([]);
      const [shown, setShown] = useState(true);
      return (
        <>
          <button type="button" onClick={() => setShown((v) => !v)} data-testid="toggle-tab">
            toggle
          </button>
          {shown && (
            <PhotoUpload taskKey="tk1" photoRefs={refs} persistedRefs={[]} onChange={setRefs} />
          )}
        </>
      );
    }

    renderWithProviders(<TabSwitcher />, { store: createStoreWithTenantRole('lead') });
    const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
    await user.upload(input as HTMLInputElement, new File(['x'], 'p.jpg', { type: 'image/jpeg' }));
    expect(await screen.findByTestId('photo-remove-0')).toBeInTheDocument();

    // Away and back — the unmount that used to erase "staged".
    await user.click(screen.getByTestId('toggle-tab'));
    await waitFor(() => expect(screen.queryByTestId('photo-upload')).toBeNull());
    await user.click(screen.getByTestId('toggle-tab'));

    expect(await screen.findByTestId('photo-remove-0')).toBeInTheDocument();
  });

  it('keeps the photos that did upload when a later file in the batch fails', async () => {
    const user = userEvent.setup();
    server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
    let call = 0;
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/photos', () => {
        call += 1;
        // First file stored, second rejected — a quota, MIME or network failure
        // partway through a multi-file selection.
        if (call === 1) return HttpResponse.json(attachment());
        return HttpResponse.json({ message: 'boom' }, { status: 500 });
      }),
    );
    const onChange = vi.fn();

    renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
      store: createStoreWithTenantRole('lead'),
    });
    const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
    await user.upload(input as HTMLInputElement, [
      new File(['a'], 'a.jpg', { type: 'image/jpeg' }),
      new File(['b'], 'b.jpg', { type: 'image/jpeg' }),
    ]);

    // The first attachment is stored server-side either way. Dropping it from local
    // state would make it an orphan counting against the tenant quota — and with the
    // sweep shipped disabled, nothing would ever collect it.
    await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));
  });

  it('does not offer to remove a photo while the rest of the batch is still uploading', async () => {
    const user = userEvent.setup();
    server.use(http.get(ATTACHMENT_URI, () => blobResponse()));
    let release: (() => void) | undefined;
    const secondFileHangs = new Promise<void>((resolve) => {
      release = resolve;
    });
    let call = 0;
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/photos', async () => {
        call += 1;
        if (call === 1) return HttpResponse.json(attachment());
        // Still in flight: this is the window the per-file `onChange` opened.
        await secondFileHangs;
        return HttpResponse.json(attachment('att-2'));
      }),
    );
    const onChange = vi.fn();

    renderWithProviders(<Harness initial={[]} onChange={onChange} />, {
      store: createStoreWithTenantRole('lead'),
    });
    const input = screen.getByTestId('photo-upload').querySelector('input[type="file"]')!;
    await user.upload(input as HTMLInputElement, [
      new File(['a'], 'a.jpg', { type: 'image/jpeg' }),
      new File(['b'], 'b.jpg', { type: 'image/jpeg' }),
    ]);

    // File 1 has been handed to the parent, so its remove control now renders — but
    // clicking it mid-batch deletes the attachment while the loop still holds
    // `att-1` in its own snapshot, and the loop's next `onChange` puts the deleted id
    // straight back. The list then shows a broken image and `complete` answers 422.
    await waitFor(() => expect(onChange).toHaveBeenCalledWith(['att-1']));
    const remove = await screen.findByRole('button', { name: /entfernen|remove/i });
    expect(remove).toBeDisabled();

    release!();
  });
});
