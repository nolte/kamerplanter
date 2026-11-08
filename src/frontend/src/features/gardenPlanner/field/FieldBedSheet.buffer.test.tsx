import 'fake-indexeddb/auto';
import { configureStore } from '@reduxjs/toolkit';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { SnackbarProvider } from 'notistack';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { rootReducer } from '@/store/rootReducer';
import { authState, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { completeWrite, emptyWriteQueue, noteWrite, testWriteQueueDatabase } from '@/test/writeQueueTestKit';
import { ThemeContextProvider } from '@/theme';
import * as imageNormalization from '@/utils/imageNormalization';
import { bedListItem } from '../bed/bedTestKit';
import { BASE, careTask, useCareBackend } from '../care/careTestKit';
import { QUEUE_CAPACITY, enqueue, listEntries, newClientEventId, updateEntry } from '../offline/queue';
import type { QueueEntry } from '../offline/queueTypes';
import FieldBedSheet from './FieldBedSheet';

/**
 * REQ-053 WP 9.4 (#2744), GP-UX-024 part 2 — field mode with the offline write buffer: offline, "Done", the note
 * and the photos are buffered with their capture time (and "Undo" takes them out again), every other write stays
 * locked, a lost answer online is buffered with the SAME id it was sent with, and a full buffer takes nothing more.
 */

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

const SCOPE = { userKey: 'user-1', tenantKey: 'tenant-1' };
const BED = bedListItem('loc_a', { name: 'Raised bed 1' });

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function Sheet() {
  const online = useOnlineStatus();
  return <FieldBedSheet bed={BED} online={online} onClose={() => undefined} onChanged={() => undefined} onPlanChanged={() => undefined} />;
}

function renderSheet() {
  const store = configureStore({ reducer: rootReducer, preloadedState: { ...tenantState('grower'), ...authState() } as never });
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <MemoryRouter>
            <Sheet />
          </MemoryRouter>
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
}

function useBackend() {
  const care = useCareBackend([careTask('t_water', { name: 'Water the bed', category: 'watering', entity_key: 'loc_a' })]);
  server.use(
    http.get(`${BASE}/locations/:key/plant-states`, () =>
      HttpResponse.json([
        {
          plant_key: 'pl_1',
          slot_key: null,
          instance_id: 'PL_1',
          species_key: 'sp_tomato',
          species_name: 'Tomato',
          planted_on: '2026-05-01',
          lifecycle: 'active',
          phase: null,
          last_care: {},
          attention: [],
          harvest: { ready: false },
          inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0 },
        },
      ]),
    ),
  );
  return care;
}

/** A sheet loaded online, then the connection goes. */
async function offlineSheet() {
  renderSheet();
  const sheet = await screen.findByTestId('field-bed-sheet');
  await within(sheet).findByTestId('field-done-t_water');
  setOnline(false);
  await within(sheet).findByTestId('field-sheet-offline');
  return sheet;
}

beforeAll(() => setActiveTenantSlug('testgarten'));

beforeEach(async () => {
  setOnline(true);
  await emptyWriteQueue();
  localStorage.clear();
});

afterEach(() => {
  setOnline(true);
  vi.restoreAllMocks();
  cleanup();
});

describe('offline with the buffer', () => {
  it('buffers "Done" with its capture time, shows the task as waiting and sends nothing', async () => {
    const { seen } = useBackend();
    const user = userEvent.setup();
    const sheet = await offlineSheet();
    expect(within(sheet).getByTestId('field-sheet-offline')).toHaveTextContent(/stored on this device/);

    const before = Date.now();
    await user.click(within(sheet).getByTestId('field-done-t_water'));
    await user.click(within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit'));

    expect(await within(sheet).findByTestId('field-done-queued-t_water')).toHaveTextContent('Waiting to be sent');
    expect(within(sheet).queryByTestId('field-done-t_water')).toBeNull();
    const [entry] = await listEntries(SCOPE);
    expect(entry).toMatchObject({ status: 'pending', bedKey: 'loc_a', bedName: 'Raised bed 1' });
    expect(entry.write).toMatchObject({ kind: 'complete', taskKey: 't_water', taskName: 'Water the bed' });
    const performedAt = Date.parse((entry.write as Extract<QueueEntry['write'], { kind: 'complete' }>).payload.performed_at!);
    expect(performedAt).toBeGreaterThanOrEqual(before - 1000);
    expect(seen.filter((request) => request.url.includes('/complete'))).toHaveLength(0);
  });

  it('"Undo" takes a buffered entry out of the buffer', async () => {
    useBackend();
    const user = userEvent.setup();
    const sheet = await offlineSheet();
    await user.click(within(sheet).getByTestId('field-done-t_water'));
    await user.click(within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit'));
    await user.click(await screen.findByTestId('care-undo'));
    await waitFor(async () => expect(await listEntries(SCOPE)).toEqual([]));
    expect(await within(sheet).findByTestId('field-done-t_water')).toBeEnabled();
  });

  it('keeps every other chip locked and buffers the note', async () => {
    useBackend();
    const user = userEvent.setup();
    const sheet = await offlineSheet();
    for (const id of ['watering', 'harvest', 'sowing', 'weeding', 'planted']) {
      expect(within(sheet).getByTestId(`field-chip-${id}`)).toBeDisabled();
    }
    expect(within(sheet).getByTestId('field-chips-offline-hint')).toBeInTheDocument();
    await user.click(within(sheet).getByTestId('field-chip-note'));
    const dialog = await screen.findByTestId('care-log-dialog');
    await user.type(within(dialog).getByTestId('care-log-note'), 'Snails at the lettuce');
    await user.click(within(dialog).getByTestId('care-log-submit'));
    await waitFor(() => expect(screen.queryByTestId('care-log-dialog')).toBeNull());
    const [entry] = await listEntries(SCOPE);
    expect(entry.write).toMatchObject({ kind: 'note', body: { location_key: 'loc_a', category: 'note' } });
    expect((entry.write as Extract<QueueEntry['write'], { kind: 'note' }>).body.summary).toContain('Snails at the lettuce');
  });

  it('buffers a photo of the bed, downscaled to 1920 px and JPEG 80', async () => {
    useBackend();
    const scaled = new File([new Uint8Array([9, 9])], 'bed.jpg', { type: 'image/jpeg' });
    const normalize = vi
      .spyOn(imageNormalization, 'normalizeImage')
      .mockResolvedValue({ file: scaled, previewUrl: 'blob:scaled' });
    const user = userEvent.setup();
    const sheet = await offlineSheet();
    await user.click(within(sheet).getByTestId('field-bed-photo'));
    const dialog = await screen.findByTestId('plant-photo-upload-dialog');
    await user.click(within(dialog).getByTestId('mock-pick-image'));
    await user.click(within(dialog).getByTestId('plant-photo-upload-confirm'));
    expect(await screen.findByText('Photo stored on this device — it is sent as soon as you are online.')).toBeInTheDocument();
    expect(normalize).toHaveBeenLastCalledWith(expect.any(File), { maxEdge: 1920, quality: 0.8 });
    const [entry] = await listEntries(SCOPE);
    expect(entry.write).toMatchObject({ kind: 'bedPhoto', locationKey: 'loc_a', photo: { type: 'image/jpeg', name: 'photo.jpg' } });
    expect(new Uint8Array((entry.write as Extract<QueueEntry['write'], { kind: 'bedPhoto' }>).photo.bytes)).toEqual(
      new Uint8Array([9, 9]),
    );
  });

  it('takes nothing more when the buffer is full (R-019)', async () => {
    useBackend();
    const rows: QueueEntry[] = Array.from({ length: QUEUE_CAPACITY }, (_, index) => ({
      id: newClientEventId(),
      ...SCOPE,
      capturedAt: index,
      status: 'pending',
      attempts: 0,
      nextAttemptAt: 0,
      syncingSince: null,
      lastErrorCode: null,
      conflictCode: null,
      kept: false,
      expiresAt: Number.MAX_SAFE_INTEGER,
      bedKey: 'loc_x',
      bedName: 'Other',
      write: noteWrite(),
    }));
    await testWriteQueueDatabase().entries.bulkAdd(rows);
    const sheet = await offlineSheet();
    expect(await within(sheet).findByTestId('field-sheet-buffer-full')).toHaveTextContent('(500 entries)');
    await waitFor(() => expect(within(sheet).getByTestId('field-done-t_water')).toBeDisabled());
    expect(within(sheet).getByTestId('field-bed-photo')).toBeDisabled();
  });
});

describe('online with the buffer', () => {
  it('buffers a completion whose answer got lost with the SAME id it was sent with', async () => {
    useBackend();
    const sent: unknown[] = [];
    server.use(
      http.post(`${BASE}/tasks/:key/complete`, async ({ request }) => {
        sent.push(((await request.json()) as { client_event_id?: unknown }).client_event_id);
        return HttpResponse.error();
      }),
    );
    const user = userEvent.setup();
    renderSheet();
    const sheet = await screen.findByTestId('field-bed-sheet');
    await user.click(await within(sheet).findByTestId('field-done-t_water'));
    await user.click(within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit'));
    await within(sheet).findByTestId('field-done-queued-t_water');
    const [entry] = await listEntries(SCOPE);
    expect(sent).toEqual([entry.id]);
  });

  async function pickBedPhoto(user: ReturnType<typeof userEvent.setup>, sheet: HTMLElement) {
    await user.click(within(sheet).getByTestId('field-bed-photo'));
    const dialog = await screen.findByTestId('plant-photo-upload-dialog');
    await user.click(within(dialog).getByTestId('mock-pick-image'));
    await user.click(within(dialog).getByTestId('plant-photo-upload-confirm'));
  }

  it("uploads a photo online as the dialog prepared it (no second encode), under a generic name", async () => {
    useBackend();
    const normalize = vi.spyOn(imageNormalization, 'normalizeImage');
    const uploads: string[] = [];
    server.use(
      http.post(`${BASE}/attachments`, async ({ request }) => {
        uploads.push(await request.text());
        return HttpResponse.json({ attachment_id: 'p_new' }, { status: 201 });
      }),
      http.post(`${BASE}/locations/:key/photos`, () =>
        HttpResponse.json({ location_key: 'loc_a', cover_photo_ref: 'p_new', photos: [], max_photos: 50 }),
      ),
    );
    const user = userEvent.setup();
    renderSheet();
    const sheet = await screen.findByTestId('field-bed-sheet');
    await within(sheet).findByTestId('field-done-t_water');
    await pickBedPhoto(user, sheet);
    await waitFor(() => expect(uploads).toHaveLength(1));
    expect(normalize).not.toHaveBeenCalled();
    expect(uploads[0]).toContain('filename="photo.jpg"');
    expect(uploads[0]).not.toContain('bed.jpg');
    expect(await listEntries(SCOPE)).toEqual([]);
  });

  it('buffers the very bytes it sent when the answer got lost, so the resend is a replay', async () => {
    useBackend();
    const normalize = vi.spyOn(imageNormalization, 'normalizeImage');
    const ids: string[] = [];
    server.use(
      http.post(`${BASE}/attachments`, async ({ request }) => {
        ids.push(/name="client_event_id"\r\n\r\n([^\r]*)/.exec(await request.text())?.[1] ?? '');
        return HttpResponse.error();
      }),
    );
    const user = userEvent.setup();
    renderSheet();
    const sheet = await screen.findByTestId('field-bed-sheet');
    await within(sheet).findByTestId('field-done-t_water');
    await pickBedPhoto(user, sheet);
    await waitFor(async () => expect(await listEntries(SCOPE)).toHaveLength(1));
    const [entry] = await listEntries(SCOPE);
    expect(ids).toEqual([entry.id]);
    expect(normalize).not.toHaveBeenCalled();
    const photo = (entry.write as Extract<QueueEntry['write'], { kind: 'bedPhoto' }>).photo;
    expect(new Uint8Array(photo.bytes)).toEqual(new Uint8Array([1, 2, 3]));
    expect(photo.name).toBe('photo.jpg');
  });
});

describe('the state of a buffered completion', () => {
  it('hides "Done" only while the completion is on its way; a failed one gives it back', async () => {
    useBackend();
    const entry = await enqueue({ scope: SCOPE, bedKey: 'loc_a', bedName: 'Raised bed 1', write: completeWrite('t_water') });
    await updateEntry(SCOPE, entry.seq!, { status: 'failed', attempts: 5 });
    renderSheet();
    const sheet = await screen.findByTestId('field-bed-sheet');
    expect(await within(sheet).findByTestId('field-done-t_water')).toBeEnabled();
    expect(within(sheet).queryByTestId('field-done-queued-t_water')).toBeNull();
    await updateEntry(SCOPE, entry.seq!, { status: 'pending', attempts: 0 });
    act(() => {
      window.dispatchEvent(new Event('focus'));
    });
    expect(await within(sheet).findByTestId('field-done-queued-t_water')).toBeInTheDocument();
  });
});

describe('bounded requests (review B1/B2)', () => {
  it('reads the sheet with a 15 s timeout and sends "Done" directly with the 30 s send timeout', async () => {
    useBackend();
    const { tenantClient } = await import('@/api/client');
    const get = vi.spyOn(tenantClient, 'get');
    const post = vi.spyOn(tenantClient, 'post');
    const user = userEvent.setup();
    renderSheet();
    const sheet = await screen.findByTestId('field-bed-sheet');
    await user.click(await within(sheet).findByTestId('field-done-t_water'));
    await user.click(within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit'));
    await waitFor(() => expect(post).toHaveBeenCalled());
    const reads = get.mock.calls.filter(([url]) => /tasks\/queue|plant-states/.test(String(url)));
    expect(reads.length).toBeGreaterThanOrEqual(2);
    for (const [, config] of reads) expect(config).toMatchObject({ timeout: 15_000 });
    expect(post.mock.calls[0][0]).toMatch(/tasks\/t_water\/complete/);
    expect(post.mock.calls[0][2]).toMatchObject({ timeout: 30_000 });
  });
});
