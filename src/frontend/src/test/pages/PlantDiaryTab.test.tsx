import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, type TestStore } from '@/test/helpers';
import type { PlantDiaryEntry, TenantRole } from '@/api/types';
import PlantDiaryTab from '@/pages/pflanzen/diary/PlantDiaryTab';

/**
 * REQ-051 §6.1 — the diary tab of a plant instance.
 *
 * Covers AK-14 (create/edit/delete/mark in the tab), AK-19 (a foreign entry
 * shows its state but offers no control, and a server 403 is reported in words)
 * and AK-27 (`requested` says "waiting" and shows no progress indicator).
 */

// The capture panel needs canvas/getUserMedia, neither of which jsdom has.
vi.mock('@/components/identification/ImageCapturePanel', () => ({
  default: ({ onImageReady }: { onImageReady: (f: File, url: string) => void }) => (
    <button
      type="button"
      data-testid="mock-pick-image"
      onClick={() =>
        onImageReady(
          new File([new Uint8Array([1, 2, 3])], 'p.jpg', { type: 'image/jpeg' }),
          'blob:preview',
        )
      }
    >
      pick
    </button>
  ),
}));

const PLANT_KEY = 'plant-1';
const TENANT = 'test-tenant';
const DIARY_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/diary`;
const ENTRY_URL = `${DIARY_URL}/:entryKey`;
const OVERVIEW_URL = `/api/v1/t/${TENANT}/diary`;
const ATTACHMENT_URL = `/api/v1/t/${TENANT}/attachments`;

function entry(overrides: Partial<PlantDiaryEntry> = {}): PlantDiaryEntry {
  return {
    key: 'e1',
    plant_key: PLANT_KEY,
    entry_type: 'observation',
    title: 'Braune Flecken unten',
    text: 'Seit dem Umtopfen hängen die unteren Blätter.',
    photo_refs: [],
    tags: [],
    measurements: null,
    created_by: 'u1',
    created_at: '2026-08-03T18:22:11Z',
    updated_at: '2026-08-03T18:22:11Z',
    analysis_state: 'none',
    analysis_requested_at: null,
    analysis_requested_by: null,
    analysis_claimed_at: null,
    analysis_claimed_by: null,
    analysis_lease_expires_at: null,
    analysis: null,
    analysis_error: null,
    // REQ-013 §2.3a — the fixture defaults to an entry written before the
    // environment snapshot existed, which is the shape most tests here care
    // about; the snapshot tests override it.
    environment: [],
    environment_captured_at: null,
    environment_status: 'not_attempted',
    // §7.2, evaluated server-side per entry and per user (AK-18a). The tab
    // renders this verdict; it does not derive one.
    can_request_analysis: true,
    ...overrides,
  };
}

/**
 * Register the single GET the tab issues on mount, and watch the overview.
 *
 * The tab used to fire a second request — the tenant-wide overview filtered to
 * this plant — purely to learn `can_request_analysis` and the lease-corrected
 * `analysis_state`, because the entry payload carried neither. Both now travel
 * with the entry, so the overview counter must stay at zero in every test here.
 */
function mockTab(entries: PlantDiaryEntry[]) {
  const overviewHits = { count: 0 };
  server.use(
    http.get(DIARY_URL, () => HttpResponse.json(entries)),
    http.get(OVERVIEW_URL, () => {
      overviewHits.count += 1;
      return HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 });
    }),
  );
  return overviewHits;
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

/**
 * Read a text field out of a multipart body.
 *
 * Deliberately not `await request.formData()`: under this Node/undici build the
 * parser asserts on the `file` part (`webidl.is.File`) and throws inside the
 * handler, which then looks like "the request was never made". The body itself
 * is well-formed — boundary and all — so it is read as text instead.
 */
function multipartField(body: string, name: string): string | null {
  const match = new RegExp(
    `name="${name}"(?:;[^\\r\\n]*)?\\r?\\n(?:[^\\r\\n]+\\r?\\n)*\\r?\\n([^\\r\\n]*)`,
  ).exec(body);
  return match ? match[1] : null;
}

/** Structured error envelope, as the backend's exception handlers emit it. */
function apiError(status: number, code: string) {
  return HttpResponse.json(
    {
      error_id: 'e-1',
      error_code: code,
      message: code,
      details: [],
      path: DIARY_URL,
      method: 'POST',
    },
    { status },
  );
}

describe('PlantDiaryTab (REQ-051 §6.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('lists this plant’s entries newest first (AK-14)', async () => {
    mockTab([
      entry({ key: 'e1', title: 'Neuer Eintrag' }),
      entry({ key: 'e2', title: 'Älterer Eintrag' }),
    ]);
    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    const cards = await screen.findAllByTestId('diary-entry-card');
    expect(cards).toHaveLength(2);
    expect(within(cards[0]).getByTestId('diary-entry-title')).toHaveTextContent('Neuer Eintrag');
    expect(within(cards[1]).getByTestId('diary-entry-title')).toHaveTextContent('Älterer Eintrag');
  });

  it('loads the tab with a single request — the verdict comes with the listing', async () => {
    // The listing used to be accompanied by a second GET against the
    // tenant-wide overview, filtered to this plant, whose only purpose was the
    // `can_request_analysis` verdict and the lease-corrected state. Both now
    // travel with the entry, so one request per open is enough.
    let listingRequests = 0;
    const overview = mockTab([entry({ key: 'e1' })]);
    server.use(
      http.get(DIARY_URL, () => {
        listingRequests += 1;
        return HttpResponse.json([entry({ key: 'e1' })]);
      }),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await screen.findByTestId('diary-entry-card');
    expect(listingRequests).toBe(1);
    expect(overview.count).toBe(0);
    // And the verdict was honoured, so the round trip really did carry it.
    expect(screen.getByTestId('diary-request-analysis')).toBeInTheDocument();
  });

  it('does not consult the overview after saving an entry either', async () => {
    // The save handler used to re-read the verdict for the whole plant. The
    // create/update response is a full entry, verdict included.
    const user = userEvent.setup();
    const overview = mockTab([]);
    server.use(
      http.post(DIARY_URL, () =>
        HttpResponse.json(entry({ key: 'new', title: 'Frischer Eintrag' }), { status: 201 }),
      ),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-add-entry'));
    const dialog = await screen.findByTestId('diary-entry-dialog');
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() =>
      expect(screen.getByTestId('diary-entry-title')).toHaveTextContent('Frischer Eintrag'),
    );
    expect(overview.count).toBe(0);
  });

  it('renders the state the server calls displayed, without re-deriving the lease', async () => {
    // A crashed agent: the document is stored as `in_progress`, but its lease
    // ran out, so the server answers `requested` (AK-06) — while the raw lease
    // fields stay visible as the evidence. The client renders that verdict as
    // it stands: "waiting", with the withdraw control the state allows.
    mockTab([
      entry({
        key: 'e1',
        analysis_state: 'requested',
        analysis_claimed_by: 'goose-laptop',
        analysis_claimed_at: '2026-08-04T07:10:00Z',
        analysis_lease_expires_at: '2026-08-04T07:25:00Z',
      }),
    ]);

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await screen.findByTestId('diary-entry-card');
    expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute('data-state', 'requested');
    expect(await screen.findByTestId('diary-analysis-waiting')).toBeInTheDocument();
    expect(screen.queryByTestId('diary-analysis-running')).not.toBeInTheDocument();
    expect(screen.getByTestId('diary-cancel-analysis')).toBeInTheDocument();
  });

  it('shows an empty state with a create CTA when the plant has no entries', async () => {
    mockTab([]);
    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    expect(await screen.findByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('Noch keine Tagebuch-Einträge')).toBeInTheDocument();
  });

  it('creates an entry with type, title, text and tags (AK-14)', async () => {
    const user = userEvent.setup();
    let posted: Record<string, unknown> | null = null;
    mockTab([]);
    server.use(
      http.post(DIARY_URL, async ({ request }) => {
        posted = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(entry({ key: 'new', title: 'Frischer Eintrag' }), {
          status: 201,
        });
      }),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-add-entry'));
    const dialog = await screen.findByTestId('diary-entry-dialog');

    await user.type(within(dialog).getByLabelText(/Titel/), 'Frischer Eintrag');
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.type(within(dialog).getByLabelText(/^Tags/), 'blatt{Enter}');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(posted).not.toBeNull());
    expect(posted).toMatchObject({
      entry_type: 'observation',
      title: 'Frischer Eintrag',
      text: 'Untere Blätter hängen.',
      tags: ['blatt'],
    });
    // The saved entry is spliced into the list without a full reload.
    await waitFor(() =>
      expect(screen.getByTestId('diary-entry-title')).toHaveTextContent('Frischer Eintrag'),
    );
  });

  it('edits an existing entry through the same dialog (AK-14)', async () => {
    const user = userEvent.setup();
    let put: Record<string, unknown> | null = null;
    mockTab([entry({ key: 'e1', title: 'Alt' })]);
    server.use(
      http.put(ENTRY_URL, async ({ request }) => {
        put = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(entry({ key: 'e1', title: 'Alt und geändert' }));
      }),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-entry-edit'));
    const dialog = await screen.findByTestId('diary-entry-dialog');
    const textField = within(dialog).getByLabelText(/Beschreibung/);
    await user.clear(textField);
    await user.type(textField, 'Neuer Text');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(put).not.toBeNull());
    expect(put).toMatchObject({ text: 'Neuer Text' });
    await waitFor(() =>
      expect(screen.getByTestId('diary-entry-title')).toHaveTextContent('Alt und geändert'),
    );
  });

  it('deletes an entry after confirmation (AK-14)', async () => {
    const user = userEvent.setup();
    let deleted = false;
    mockTab([entry({ key: 'e1' })]);
    server.use(
      http.delete(ENTRY_URL, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-entry-delete'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleted).toBe(true));
    await waitFor(() => expect(screen.queryByTestId('diary-entry-card')).not.toBeInTheDocument());
  });

  it('marks an entry for analysis and renders the state the server answered with (AK-14)', async () => {
    const user = userEvent.setup();
    mockTab([entry({ key: 'e1' })]);
    server.use(
      http.post(`${ENTRY_URL}/request-analysis`, () =>
        HttpResponse.json(
          entry({
            key: 'e1',
            analysis_state: 'requested',
            analysis_requested_at: '2026-08-04T07:05:00Z',
            analysis_requested_by: 'u1',
          }),
        ),
      ),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-request-analysis'));

    // The response carries the entry, not a 204, so the UI shows the state it
    // actually landed in — and withdrawing is now the offered action (AK-03).
    await waitFor(() =>
      expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute(
        'data-state',
        'requested',
      ),
    );
    expect(screen.getByTestId('diary-cancel-analysis')).toBeInTheDocument();
    expect(screen.queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
  });

  it('withdraws a marking while the entry is still unclaimed (AK-03)', async () => {
    const user = userEvent.setup();
    let cancelled = false;
    mockTab([entry({ key: 'e1', analysis_state: 'requested' })]);
    server.use(
      http.delete(`${ENTRY_URL}/request-analysis`, () => {
        cancelled = true;
        return HttpResponse.json(entry({ key: 'e1', analysis_state: 'none' }));
      }),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-cancel-analysis'));
    await waitFor(() => expect(cancelled).toBe(true));
    await waitFor(() =>
      expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute('data-state', 'none'),
    );
  });

  it('offers no withdraw control once an agent has claimed the entry (AK-03)', async () => {
    mockTab([
      entry({
        key: 'e1',
        analysis_state: 'in_progress',
        analysis_claimed_at: '2026-08-04T07:10:00Z',
        analysis_claimed_by: 'goose-laptop',
        // A live lease: the server says this entry really is being analysed.
        analysis_lease_expires_at: '2026-08-04T07:25:00Z',
      }),
    ]);

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await screen.findByTestId('diary-entry-card');
    expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute(
      'data-state',
      'in_progress',
    );
    expect(screen.queryByTestId('diary-cancel-analysis')).not.toBeInTheDocument();
    expect(screen.queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
  });

  it('shows a foreign entry’s state but no control (AK-19)', async () => {
    // `can_request_analysis: false` is the server's §7.2 verdict — someone
    // else's entry in a shared garden. The client does not re-derive it.
    mockTab([
      entry({
        key: 'e1',
        created_by: 'someone-else',
        analysis_state: 'requested',
        can_request_analysis: false,
      }),
    ]);

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await screen.findByTestId('diary-entry-card');
    expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute(
      'data-state',
      'requested',
    );
    expect(screen.queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
    expect(screen.queryByTestId('diary-cancel-analysis')).not.toBeInTheDocument();
  });

  it('reports a server-side 403 on marking in plain words (AK-19)', async () => {
    const user = userEvent.setup();
    // The listing said `true` — and the server still refuses, because the
    // verdict is a display aid and the marking endpoint re-evaluates §7.2 on
    // its own (AK-18a). With the second request gone this 403 is the only
    // remaining fallback, so it has to be reported in words.
    mockTab([entry({ key: 'e1', can_request_analysis: true })]);
    server.use(
      http.post(`${ENTRY_URL}/request-analysis`, () => apiError(403, 'PERMISSION_DENIED')),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-request-analysis'));

    expect(await screen.findByText(/nicht zur Analyse markieren/)).toBeInTheDocument();
    // The state is unchanged: a refused request must not look like a success.
    expect(screen.getByTestId('diary-analysis-state')).toHaveAttribute('data-state', 'none');
  });

  it('reports a 409 when the entry was claimed between render and click (AK-03)', async () => {
    const user = userEvent.setup();
    mockTab([entry({ key: 'e1', analysis_state: 'requested' })]);
    server.use(
      http.delete(`${ENTRY_URL}/request-analysis`, () => apiError(409, 'INVALID_STATE')),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-cancel-analysis'));
    expect(await screen.findByText(/bereits von einem Agenten übernommen/)).toBeInTheDocument();
  });

  it('states that a requested entry is waiting, without any progress indicator (AK-27)', async () => {
    mockTab([entry({ key: 'e1', analysis_state: 'requested' })]);

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    const waiting = await screen.findByTestId('diary-analysis-waiting');
    expect(waiting).toHaveTextContent(/wartet auf eine Analyse/i);
    // No bar, no spinner, no percentage: the analysing agent runs outside this
    // system, so there is nothing honest to show a duration from (§3, AK-29).
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('hides every write control for a viewer', async () => {
    mockTab([entry({ key: 'e1', can_request_analysis: false })]);
    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('viewer'),
    });

    await screen.findByTestId('diary-entry-card');
    expect(screen.queryByTestId('diary-add-entry')).not.toBeInTheDocument();
    expect(screen.queryByTestId('diary-entry-edit')).not.toBeInTheDocument();
    expect(screen.queryByTestId('diary-entry-delete')).not.toBeInTheDocument();
    expect(screen.queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
  });

  it('uploads a diary photo as an attachment of category "diary", not into the gallery', async () => {
    const user = userEvent.setup();
    let uploadedCategory: string | null = null;
    let galleryHit = false;
    mockTab([]);
    server.use(
      http.post(ATTACHMENT_URL, async ({ request }) => {
        uploadedCategory = multipartField(await request.text(), 'category');
        return HttpResponse.json(
          { attachment_id: 'att-1', mime_type: 'image/jpeg', byte_size: 3 },
          { status: 201 },
        );
      }),
      http.post(`/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/photos`, () => {
        galleryHit = true;
        return HttpResponse.json({}, { status: 201 });
      }),
      http.get(`${ATTACHMENT_URL}/:id/thumbnails/:px`, () =>
        HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
          headers: { 'Content-Type': 'image/jpeg' },
        }),
      ),
    );

    renderWithProviders(<PlantDiaryTab plantInstanceKey={PLANT_KEY} />, {
      store: storeWithRole('grower'),
    });

    await user.click(await screen.findByTestId('diary-add-entry'));
    await user.click(await screen.findByTestId('diary-add-photo'));
    await user.click(await screen.findByTestId('mock-pick-image'));
    await user.click(await screen.findByTestId('diary-photo-upload-confirm'));

    await waitFor(() => expect(uploadedCategory).toBe('diary'));
    // REQ-050 §0 pins diary photos to `category = diary`; the gallery endpoint
    // would have filed them as `category = plant` instead.
    expect(galleryHit).toBe(false);
    expect(await screen.findByTestId('diary-entry-photo-preview')).toBeInTheDocument();
  });
});
