/**
 * #1568 acceptance: the activity picker can tell "load failed" from "catalogue
 * is empty".
 *
 * **The defect.** `loadActivities` caught a failed load into `handleError` — a
 * toast — and left `allActivities` empty. The dialog then fell through to
 * `pages.tasks.noActivitiesFound`, which is the sentence for a catalogue that
 * arrived and holds nothing. So the user was told the activity does not exist
 * when in fact nobody had reached the server, and the one thing that said
 * otherwise was a toast that dismisses itself. Once the catalogue outgrew a
 * single page (#1560) it got worse rather than better: a rejection on page two
 * discards page one too, so the dialog goes from "50 of 51 rows" to "none", with
 * the same message.
 *
 * **Why the sibling file does not already cover this.** The failure case in
 * `WorkflowDetailPageCatalogueReach.test.tsx` asserts the spinner clears and the
 * toast appears. Both were already true against the defect. What it never asked
 * is the question that separates the two states — *which message does the list
 * show?* — and that is the assertion below. This is the same expression the fix
 * changes, not a neighbouring one.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { vi } from 'vitest';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';
import type { Activity, WorkflowTemplate } from '@/api/types';

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'wf-1' }) };
});

import WorkflowDetailPage from '@/pages/aufgaben/WorkflowDetailPage';

const WF_URL = '/api/v1/t/test-tenant/tasks/workflows/:key';
const TEMPLATES_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/templates';
const EXECUTIONS_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/executions';
const PHASES_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/phases';
const ACTIVITIES_URL = '/api/v1/activities';

function makeWorkflow(): WorkflowTemplate {
  return {
    key: 'wf-1',
    name: 'Tomaten-Workflow',
    description: 'Ein Workflow.',
    created_by: 'user-1',
    version: '1.0',
    species_compatible: [],
    growth_system: null,
    difficulty_level: 'beginner',
    category: 'general',
    tags: [],
    is_system: false,
    auto_generated: false,
    species_key: null,
    species_name: '',
    total_duration_days: 0,
    assigned_entity_count: 0,
    target_entity_types: ['plant_instance'],
    phase_sequence_key: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function makeActivity(index: number): Activity {
  return {
    key: `act-${index}`,
    tenant_key: 't',
    name: `Activity ${index}`,
    name_de: `Aktivität ${index}`,
    description: 'Do the thing',
    description_de: 'Mach die Sache',
    category: 'pruning',
    stress_level: 'medium',
    skill_level: 'beginner',
    recovery_days_default: 2,
    recovery_days_by_species: {},
    forbidden_phases: [],
    restricted_sub_phases: [],
    tools_required: [],
    estimated_duration_minutes: 10,
    requires_photo: false,
    species_compatible: [],
    is_system: false,
    sort_order: index,
    tags: [],
    created_at: null,
    updated_at: null,
  };
}

function serveWorkflow(activitiesResponder: Parameters<typeof http.get>[1]): void {
  server.use(
    http.get(WF_URL, () => HttpResponse.json(makeWorkflow())),
    http.get(TEMPLATES_URL, () => HttpResponse.json([])),
    http.get(EXECUTIONS_URL, () => HttpResponse.json([])),
    http.get(PHASES_URL, () => HttpResponse.json([])),
    http.get('/api/v1/species', () => HttpResponse.json({ items: [], total: 0 })),
    http.get('/api/v1/t/test-tenant/favorites', () => HttpResponse.json([])),
    http.get(ACTIVITIES_URL, activitiesResponder),
  );
}

async function openCatalogueDialog(
  user: ReturnType<typeof userEvent.setup>,
): Promise<HTMLElement> {
  await screen.findByTestId('workflow-detail-page');
  await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
  await user.click(await screen.findByTestId('add-activity-from-catalog-button'));
  const dialogs = await screen.findAllByRole('dialog');
  return dialogs[dialogs.length - 1];
}

describe('WorkflowDetailPage — failed, empty and loaded are three states (#1568)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('says the catalogue could not be loaded, and does not say it is empty', async () => {
    serveWorkflow(() => new HttpResponse(null, { status: 500 }));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-catalogue-error')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );

    // The assertion that carries the issue. Against the old code this element
    // was present with exactly this text, which is why a failed load and an
    // empty catalogue were the same screen.
    expect(within(dialog).queryByTestId('activity-catalogue-empty')).toBeNull();
    expect(within(dialog).queryByText(i18n.t('pages.tasks.noActivitiesFound'))).toBeNull();

    // A failure the user can act on: the retry control belongs to the failure
    // state and to no other.
    expect(within(dialog).getByTestId('error-retry-button')).toBeTruthy();
  });

  it('recovers through the retry control instead of needing the dialog reopened', async () => {
    let attempts = 0;
    serveWorkflow(() => {
      attempts += 1;
      if (attempts === 1) return new HttpResponse(null, { status: 500 });
      return HttpResponse.json([makeActivity(0)]);
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);
    await waitFor(
      () => {
        expect(within(dialog).getByTestId('error-retry-button')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );

    await user.click(within(dialog).getByTestId('error-retry-button'));

    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-row-act-0')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(within(dialog).queryByTestId('activity-catalogue-error')).toBeNull();
    // The counterpart the positive assertion needs: without a second request
    // the row above could not exist, so this pins the retry to the network
    // rather than to a re-render.
    expect(attempts).toBeGreaterThan(1);
  });

  it('says the catalogue is empty only when the catalogue actually arrived empty', async () => {
    serveWorkflow(() => HttpResponse.json([]));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-catalogue-empty')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(
      within(dialog).getByText(i18n.t('pages.tasks.activityCatalogueEmpty')),
    ).toBeTruthy();
    // Distinct from the failure state, which is the whole point of the pair.
    expect(within(dialog).queryByTestId('activity-catalogue-error')).toBeNull();
  });

  it('separates an empty catalogue from a search that matched nothing', async () => {
    // Both render "nothing to pick", and they are still two different sentences:
    // one is the state of the catalogue, the other the state of the search box.
    serveWorkflow(() => HttpResponse.json([makeActivity(0)]));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);
    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-row-act-0')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );

    const search = within(dialog).getByTestId('activity-catalogue-search');
    await user.click(within(search).getByRole('textbox'));
    await user.paste('zzz-kein-treffer');

    await waitFor(
      () => {
        expect(
          within(dialog).getByText(i18n.t('pages.tasks.noActivitiesFound')),
        ).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(
      within(dialog).queryByText(i18n.t('pages.tasks.activityCatalogueEmpty')),
    ).toBeNull();
  });
});

/**
 * The perceivable half, and the empty state's way out (#1568 UI review).
 *
 * The cases above assert which element is on screen. None asked how a user who
 * cannot see it learns that the catalogue arrived, and none asked where focus
 * goes when the retry control unmounts under the click that hit it. Of the three
 * transitions only `→ failed` announced itself for free, through the native
 * `role="alert"` inside MUI's `Alert`.
 *
 * Which code makes each red, recorded because a case that passes against the
 * unrepaired version certifies nothing:
 *
 * | case | red against |
 * |---|---|
 * | announces while loading | removing `<LoadingStatus>` |
 * | focus after a successful retry | removing `useRetryFocus` |
 * | CTA on an empty catalogue | removing the button |
 * | no CTA on a search miss | rendering the button unconditionally |
 */
describe('WorkflowDetailPage — the activity catalogue is perceivable (#1568 UI review)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('announces the load in a live region alongside the spinner', async () => {
    // Released in `finally`: a request left hanging keeps its entry in
    // `useCatalogue`'s module-level in-flight map, and every later case in the
    // file then joins a dead promise. Measured on the sibling file.
    let release!: () => void;
    const arrives = new Promise<void>((resolve) => {
      release = resolve;
    });
    serveWorkflow(async () => {
      await arrives;
      return HttpResponse.json([makeActivity(0)]);
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    try {
      const status = within(dialog).getByTestId('activity-catalogue-loading-status');
      expect(status.getAttribute('role')).toBe('status');
      expect(status.getAttribute('aria-live')).toBe('polite');
      // A named region with no content announces nothing, so the text matters.
      expect(status.textContent).toBe(i18n.t('common.loading'));
      // The spinner is the R-020 half and is invisible to a screen reader.
      expect(within(dialog).getByTestId('activity-catalogue-loading')).toBeTruthy();
    } finally {
      release();
    }

    await waitFor(
      () => {
        expect(
          within(dialog).getByTestId('activity-catalogue-loading-status').textContent,
        ).toBe('');
      },
      { timeout: WAIT_BUDGET },
    );
  });

  it('puts focus on the search box after a retry succeeds', async () => {
    let attempts = 0;
    serveWorkflow(() => {
      attempts += 1;
      if (attempts === 1) return new HttpResponse(null, { status: 500 });
      return HttpResponse.json([makeActivity(0)]);
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);
    await user.click(await within(dialog).findByTestId('error-retry-button'));

    await waitFor(
      () => {
        expect(within(dialog).queryByTestId('activity-catalogue-error')).toBeNull();
      },
      { timeout: WAIT_BUDGET },
    );

    // Against the unrepaired version the focused button unmounted with its
    // branch and the browser fell back to `<body>`.
    const search = within(within(dialog).getByTestId('activity-catalogue-search')).getByRole(
      'textbox',
    );
    await waitFor(
      () => {
        expect(document.activeElement).toBe(search);
      },
      { timeout: WAIT_BUDGET },
    );
    expect(document.activeElement).not.toBe(document.body);
  });

  it('offers a call to action when the catalogue itself is empty', async () => {
    serveWorkflow(() => HttpResponse.json([]));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    const cta = await within(dialog).findByTestId('activity-catalogue-empty-cta');
    // R-014: the label names where it goes, rather than "OK" or "Weiter".
    expect(cta.textContent).toBe(i18n.t('pages.tasks.activityCatalogueEmptyCta'));
  });

  it('offers no call to action when only the search matched nothing', async () => {
    // The counterpart that keeps the case above honest: an unconditional button
    // would satisfy it. A search miss is not an empty catalogue, and its way out
    // is the search box the user is already looking at.
    serveWorkflow(() => HttpResponse.json([makeActivity(0)]));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);
    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-row-act-0')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );

    const search = within(dialog).getByTestId('activity-catalogue-search');
    await user.click(within(search).getByRole('textbox'));
    await user.paste('zzz-kein-treffer');

    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-catalogue-empty')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(within(dialog).queryByTestId('activity-catalogue-empty-cta')).toBeNull();
  });
});
