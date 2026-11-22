/**
 * #3065: the task queue's care-profile dialog must only ever show the profile
 * of the plant it was opened for.
 *
 * The dialog used to open in the same tick as the profile read and render
 * whatever profile the shared `careReminders` slice still held — the plant
 * edited before. When the read resolved, the form re-seeded every field from
 * the new object and discarded the user's input (the nightly E2E "month click
 * does nothing"); a save in that window wrote a form seeded from the other
 * plant. A late answer for an earlier plant re-seeded the form the same way.
 *
 * Every profile read here is held back until the test releases it, so the
 * window between opening and loading is observable.
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { CareDashboardEntry, CareProfile } from '@/api/types';
import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';
const TIMEOUT = { timeout: 10000 } as const;

function makeEntry(plantKey: string, plantName: string): CareDashboardEntry {
  return {
    plant_key: plantKey,
    plant_name: plantName,
    species_name: null,
    reminder_type: 'fertilizing',
    urgency: 'overdue',
    due_date: '2024-01-01',
    care_profile_key: `cp-${plantKey}`,
    task_key: null,
  };
}

function makeProfile(plantKey: string, months: number[]): CareProfile {
  return {
    key: `cp-${plantKey}`,
    care_style: 'tropical',
    watering_interval_days: 7,
    winter_watering_multiplier: 1.0,
    watering_method: 'top_water',
    water_quality_hint: null,
    fertilizing_interval_days: 14,
    fertilizing_active_months: months,
    repotting_interval_months: 12,
    pest_check_interval_days: 7,
    location_check_enabled: false,
    location_check_months: [],
    humidity_check_enabled: false,
    humidity_check_interval_days: 3,
    adaptive_learning_enabled: false,
    auto_create_watering_task: true,
    auto_create_fertilizing_task: true,
    auto_create_repotting_task: false,
    auto_create_pest_check_task: false,
    watering_interval_learned: null,
    fertilizing_interval_learned: null,
    notes: null,
    auto_generated: true,
    plant_key: plantKey,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

// Plant A fertilises March–September, plant B April–August: month 3 tells them apart.
const PROFILES: Record<string, CareProfile> = {
  'plant-a': makeProfile('plant-a', [3, 4, 5, 6, 7, 8, 9]),
  'plant-b': makeProfile('plant-b', [4, 5, 6, 7, 8]),
};

/** Profile reads answer only once released; each read waits for its own release. */
let pending: Array<{ plantKey: string; release: () => void }>;
let failNext: Set<string>;
let answered: string[];

/** Releases the oldest (default) or the newest held-back read for `plantKey`. */
function release(plantKey: string, which: 'oldest' | 'newest' = 'oldest') {
  const matching = pending.flatMap((p, i) => (p.plantKey === plantKey ? [i] : []));
  const index = (which === 'oldest' ? matching[0] : matching[matching.length - 1]) ?? -1;
  if (index < 0) throw new Error(`no pending profile read for ${plantKey}`);
  const [entry] = pending.splice(index, 1);
  act(() => entry.release());
}

async function waitForRead(plantKey: string) {
  await waitFor(() => expect(pending.some((p) => p.plantKey === plantKey)).toBe(true), TIMEOUT);
}

function month(n: number) {
  return screen.getByTestId(`fertilizing-month-${n}`);
}

/** Clicks the row's edit button and waits until the profile read has been sent. */
async function openEditor(plantKey: string) {
  const before = pending.filter((p) => p.plantKey === plantKey).length;
  const button = await screen.findByTestId(`care-edit-profile-care-${plantKey}-fertilizing`, {}, TIMEOUT);
  await userEvent.click(button);
  await waitFor(
    () => expect(pending.filter((p) => p.plantKey === plantKey)).toHaveLength(before + 1),
    TIMEOUT,
  );
}

/**
 * Waits until the held-back answer for `plantKey` has left the mock server and
 * the page has had the macrotasks it needs to take it in (axios → thunk →
 * reducer → render). The red run of the revert proof is what shows this is
 * long enough: with the pre-#3065 code the late answer re-seeds the form
 * inside this window.
 */
async function settleAnswer(plantKey: string, answers = 1) {
  await waitFor(
    () => expect(answered.filter((k) => k === plantKey).length).toBeGreaterThanOrEqual(answers),
    TIMEOUT,
  );
  for (let i = 0; i < 5; i += 1) {
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

async function closeEditor() {
  await userEvent.click(within(screen.getByTestId('care-profile-edit-dialog')).getByTestId('cancel-button'));
  await waitFor(() => expect(screen.queryByTestId('care-profile-edit-dialog')).toBeNull(), TIMEOUT);
}

describe('TaskQueuePage — care-profile dialog loads the profile of its own plant (#3065)', () => {
  beforeEach(() => {
    pending = [];
    failNext = new Set();
    answered = [];
    server.use(
      http.get(`${TASKS}/queue`, () => HttpResponse.json([])),
      http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
      http.get(TASKS, () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/plant-instances', () => HttpResponse.json([])),
      http.get(`${CARE}/dashboard`, () =>
        HttpResponse.json([makeEntry('plant-a', 'Tomate'), makeEntry('plant-b', 'Basilikum')]),
      ),
      http.get('/api/v1/care-reminders/plants/:key/profile', async ({ params }) => {
        const plantKey = String(params.key);
        await new Promise<void>((resolve) => pending.push({ plantKey, release: resolve }));
        answered.push(plantKey);
        if (failNext.delete(plantKey)) {
          return HttpResponse.json({ error_code: 'INTERNAL_ERROR' }, { status: 500 });
        }
        return HttpResponse.json(PROFILES[plantKey]);
      }),
    );
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    // Let held-back reads finish so no handler outlives its test.
    for (const p of pending) p.release();
    cleanup();
  });

  it('never shows the previous plant\'s form while the next plant\'s profile loads', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    // Edit plant A once, so its profile is the one the shared slice holds.
    await openEditor('plant-a');
    release('plant-a');
    await waitFor(() => expect(month(3)).toHaveAttribute('aria-pressed', 'true'), TIMEOUT);
    await closeEditor();

    // Open plant B: until B's profile has arrived there is no form at all —
    // in particular not plant A's.
    await openEditor('plant-b');
    expect(screen.queryByTestId('care-profile-form')).toBeNull();
    const dialog = screen.getByTestId('care-profile-edit-dialog');
    expect(within(dialog).getByTestId('loading-skeleton')).toHaveAttribute('aria-busy', 'true');

    release('plant-b');
    await within(dialog).findByTestId('care-profile-form', {}, TIMEOUT);
    // B's months, not A's.
    expect(month(3)).toHaveAttribute('aria-pressed', 'false');
    expect(month(4)).toHaveAttribute('aria-pressed', 'true');
  });

  it('keeps an edit made after load when an earlier plant\'s answer arrives late', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    // Plant A's read is still in flight when the user dismisses the editor and
    // moves on to B.
    await openEditor('plant-a');
    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByTestId('care-profile-edit-dialog')).toBeNull(), TIMEOUT);

    await openEditor('plant-b');
    release('plant-b');
    await screen.findByTestId('care-profile-form', {}, TIMEOUT);

    // The user switches October on — the click the nightly E2E saw "do nothing".
    await userEvent.click(month(10));
    expect(month(10)).toHaveAttribute('aria-pressed', 'true');

    // A's answer lands now. It must not re-seed B's form.
    release('plant-a');
    await settleAnswer('plant-a');
    expect(month(10)).toHaveAttribute('aria-pressed', 'true');
    expect(month(3)).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByTestId('care-profile-dirty-hint')).toBeInTheDocument();
  });

  // Same plant, two reads in flight: the editor is dismissed and reopened for A
  // before A's first read answered. A guard keyed on the plant lets that first
  // answer through after the second one, and the form re-seeds over the edit.
  it('keeps an edit when the editor is reopened for the same plant and the first read answers late', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await openEditor('plant-a');
    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByTestId('care-profile-edit-dialog')).toBeNull(), TIMEOUT);

    await openEditor('plant-a');
    release('plant-a', 'newest');
    await screen.findByTestId('care-profile-form', {}, TIMEOUT);
    await userEvent.click(month(10));
    expect(month(10)).toHaveAttribute('aria-pressed', 'true');

    release('plant-a', 'oldest');
    await settleAnswer('plant-a', 2);
    expect(month(10)).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('care-profile-dirty-hint')).toBeInTheDocument();
  });

  it('shows a retryable error instead of a form when the profile read fails', async () => {
    failNext.add('plant-b');
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await openEditor('plant-b');
    const dialog = screen.getByTestId('care-profile-edit-dialog');
    release('plant-b');

    const retry = await within(dialog).findByTestId('error-retry-button', {}, TIMEOUT);
    expect(within(dialog).queryByTestId('care-profile-form')).toBeNull();

    await userEvent.click(retry);
    await waitForRead('plant-b');
    release('plant-b');
    await within(dialog).findByTestId('care-profile-form', {}, TIMEOUT);
    expect(month(4)).toHaveAttribute('aria-pressed', 'true');
  });
});
