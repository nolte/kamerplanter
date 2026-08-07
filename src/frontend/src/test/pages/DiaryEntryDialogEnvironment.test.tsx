import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, type TestStore } from '@/test/helpers';
import type { PlantDiaryEntry, PlantEnvironmentPreview, TenantRole } from '@/api/types';
import DiaryEntryDialog from '@/pages/pflanzen/diary/DiaryEntryDialog';

/**
 * REQ-013 §2.3a — the environment snapshot in the create dialog.
 *
 * The dialog's whole job here is to be *honest*: show what will be stored, let
 * the author decline it, and never pretend a value is editable. The tests below
 * pin those three, plus the two invariants that make the feature worth having —
 * the client never sends readings, and nothing automatic touches `measurements`.
 */

const PLANT_KEY = 'plant-1';
const TENANT = 'test-tenant';
const DIARY_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/diary`;
const ENVIRONMENT_URL = `/api/v1/t/${TENANT}/plant-instances/${PLANT_KEY}/environment`;

function storeWithRole(role: TenantRole = 'grower'): TestStore {
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

function savedEntry(overrides: Partial<PlantDiaryEntry> = {}): PlantDiaryEntry {
  return {
    key: 'e-new',
    plant_key: PLANT_KEY,
    entry_type: 'problem',
    title: null,
    text: 'Untere Blätter hängen.',
    photo_refs: [],
    tags: [],
    measurements: null,
    created_by: 'u1',
    created_at: '2026-08-03T18:22:11Z',
    updated_at: '2026-08-03T18:22:11Z',
    environment: [],
    environment_captured_at: null,
    environment_status: 'not_attempted',
    analysis_state: 'none',
    analysis_requested_at: null,
    analysis_requested_by: null,
    analysis_claimed_at: null,
    analysis_claimed_by: null,
    analysis_lease_expires_at: null,
    analysis: null,
    analysis_error: null,
    can_request_analysis: true,
    ...overrides,
  };
}

const CAPTURED_PREVIEW: PlantEnvironmentPreview = {
  plant_key: PLANT_KEY,
  captured_at: '2026-08-03T18:22:03Z',
  environment_status: 'captured',
  readings: [
    {
      metric_type: 'temperature_celsius',
      value: 31.2,
      unit: '°C',
      source: 'ha_auto',
      measured_at: '2026-08-03T18:21:44Z',
      sensor_key: 's-temp',
      origin: 'location',
    },
    {
      metric_type: 'humidity_percent',
      value: 28,
      unit: '%',
      source: 'open-meteo',
      measured_at: '2026-08-03T18:10:00Z',
      sensor_key: null,
      origin: 'weather',
    },
  ],
};

function mockPreview(body: PlantEnvironmentPreview | null, status = 200) {
  const hits = { count: 0 };
  server.use(
    http.get(ENVIRONMENT_URL, () => {
      hits.count += 1;
      return body !== null && status === 200
        ? HttpResponse.json(body)
        : new HttpResponse(null, { status });
    }),
  );
  return hits;
}

/** Register the create endpoint and capture the body it was called with. */
function mockCreate() {
  const captured: { body: Record<string, unknown> | null } = { body: null };
  server.use(
    http.post(DIARY_URL, async ({ request }) => {
      captured.body = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(savedEntry(), { status: 201 });
    }),
  );
  return captured;
}

function renderDialog(entry: PlantDiaryEntry | null = null) {
  const onSaved = vi.fn();
  const onClose = vi.fn();
  renderWithProviders(
    <DiaryEntryDialog
      open
      plantInstanceKey={PLANT_KEY}
      entry={entry}
      onSaved={onSaved}
      onClose={onClose}
    />,
    { store: storeWithRole() },
  );
  return { onSaved, onClose };
}

describe('DiaryEntryDialog — environment snapshot', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // The user-facing strings are German (DE is canonical), and the assertions
    // below read them — a default English run would test a different product.
    i18n.changeLanguage('de');
  });

  it('shows what the capture would store, with origin and measurement time', async () => {
    mockPreview(CAPTURED_PREVIEW);
    renderDialog();

    const section = await screen.findByTestId('diary-environment-section');
    await screen.findByTestId('diary-environment-preview-row-temperature_celsius');

    const temp = within(section).getByTestId('diary-environment-preview-row-temperature_celsius');
    expect(temp).toHaveTextContent('31.2 °C');
    // Where it was measured — a probe in the plant's own location is different
    // evidence from a weather service, and the reader has to be able to tell.
    expect(
      within(section).getByTestId('diary-environment-preview-origin-temperature_celsius'),
    ).toHaveTextContent('Standort');
    expect(
      within(section).getByTestId('diary-environment-preview-origin-humidity_percent'),
    ).toHaveTextContent('Wetterdienst');
    // The provenance travels into the UI, not just into the document.
    expect(temp).toHaveTextContent('ha_auto');
  });

  it('offers no way to edit an automatic value', async () => {
    mockPreview(CAPTURED_PREVIEW);
    renderDialog();

    const section = await screen.findByTestId('diary-environment-section');
    // A corrected sensor reading is a manual measurement and belongs in the
    // `measurements` editor. An input here would produce a value that looks
    // automatic and is not.
    expect(within(section).queryByRole('textbox')).toBeNull();
    expect(within(section).queryByRole('spinbutton')).toBeNull();
  });

  it('says which kind of empty it is when nothing covers the plant', async () => {
    mockPreview({
      plant_key: PLANT_KEY,
      captured_at: '2026-08-03T18:22:03Z',
      environment_status: 'no_source',
      readings: [],
    });
    renderDialog();

    const empty = await screen.findByTestId('diary-environment-empty');
    // "attach a sensor" — actionable, and different from "sensors unreachable".
    expect(empty).toHaveTextContent(/keine aktuellen Sensorwerte/i);
    expect(empty).toHaveTextContent(/Sensor an den Standort/i);
  });

  it('says something different when the sensors could not be reached', async () => {
    mockPreview({
      plant_key: PLANT_KEY,
      captured_at: '2026-08-03T18:22:03Z',
      environment_status: 'unavailable',
      readings: [],
    });
    renderDialog();

    expect(await screen.findByTestId('diary-environment-empty')).toHaveTextContent(
      /nicht erreichbar/i,
    );
  });

  it('captures by default and sends only the permission, never the readings', async () => {
    mockPreview(CAPTURED_PREVIEW);
    const created = mockCreate();
    const user = userEvent.setup();
    renderDialog();

    const dialog = await screen.findByTestId('diary-entry-dialog');
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created.body).not.toBeNull());
    expect(created.body?.capture_environment).toBe(true);
    // The load-bearing one: a client that could send readings could invent them,
    // and this field is meant to be evidence.
    expect(created.body).not.toHaveProperty('environment');
    expect(created.body).not.toHaveProperty('environment_status');
    expect(created.body).not.toHaveProperty('environment_captured_at');
  });

  it('sends the opt-out when the author clears the checkbox', async () => {
    mockPreview(CAPTURED_PREVIEW);
    const created = mockCreate();
    const user = userEvent.setup();
    renderDialog();

    const dialog = await screen.findByTestId('diary-entry-dialog');
    await screen.findByTestId('diary-environment-preview-row-temperature_celsius');
    await user.click(within(dialog).getByTestId('diary-environment-capture-toggle'));
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created.body).not.toBeNull());
    expect(created.body?.capture_environment).toBe(false);
  });

  it('never mixes an automatic reading into the grower measurements', async () => {
    mockPreview(CAPTURED_PREVIEW);
    const created = mockCreate();
    const user = userEvent.setup();
    renderDialog();

    const dialog = await screen.findByTestId('diary-entry-dialog');
    await screen.findByTestId('diary-environment-preview-row-temperature_celsius');
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.click(within(dialog).getByTestId('diary-measurement-add'));
    const row = within(dialog).getByTestId('diary-measurement-row');
    await user.type(within(row).getByLabelText(/Bezeichnung/), 'height_cm');
    await user.type(within(row).getByLabelText(/Wert/), '84');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created.body).not.toBeNull());
    // Exactly what the grower typed — the previewed 31.2 °C is nowhere near it.
    expect(created.body?.measurements).toEqual({ height_cm: 84 });
  });

  it('saves the entry even when the preview could not be loaded', async () => {
    // A grower documenting a problem is the worst moment to be blocked by a
    // sensor. The failed preview is silent and the save is unaffected.
    mockPreview(null, 503);
    const created = mockCreate();
    const user = userEvent.setup();
    const { onSaved } = renderDialog();

    const dialog = await screen.findByTestId('diary-entry-dialog');
    await screen.findByTestId('diary-environment-empty');
    await user.type(within(dialog).getByLabelText(/Beschreibung/), 'Untere Blätter hängen.');
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(created.body?.capture_environment).toBe(true);
  });

  it('does not preview or offer the opt-out when editing an existing entry', async () => {
    // Editing never re-captures server-side, so a preview here would advertise
    // a climate the save is not going to store.
    const hits = mockPreview(CAPTURED_PREVIEW);
    renderDialog(savedEntry({ text: 'Alter Text' }));

    await screen.findByTestId('diary-entry-dialog');
    await waitFor(() => expect(screen.getByDisplayValue('Alter Text')).toBeInTheDocument());
    expect(screen.queryByTestId('diary-environment-section')).toBeNull();
    expect(hits.count).toBe(0);
  });
});
