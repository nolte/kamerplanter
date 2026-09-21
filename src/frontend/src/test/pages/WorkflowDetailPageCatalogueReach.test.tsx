/**
 * #1530 acceptance: the workflow's "add activity from catalogue" dialog offers
 * the **whole** activity catalogue, not the first page of it.
 *
 * The defect and why it was invisible: `loadActivities` fetched with
 * `listActivities()`, whose signature is `listActivities(params?, offset = 0,
 * limit = 50)` — a bound applied by the *client*, so it holds no matter what the
 * server would have answered. Every control in the dialog (the favourites and
 * species-compatible chips, the search box) then narrows that array
 * client-side. So the catalogue's last rows do not arrive late or render
 * partially; they are absent, and the dialog answers "no such activity" with the
 * same empty list it shows for a genuine miss. The seeded catalogue is 51 rows
 * (`grep -c '^  - name: ' app/migrations/seed_data/activities.yaml`), so the
 * picker was already one row short before any tenant added an activity.
 *
 * Same class as #956/#995 (fertilizers), #1503/#1526 (task queue): a caller that
 * needs a complete catalogue reading through a capped reader.
 *
 * This drives the real page, the real endpoint layer and the real
 * `fetchAllPages` loop against a handler that pages the way the backend does.
 * The paging loop's own termination rule is covered in
 * `src/test/api/endpoints/activities.test.ts`; what this file asks is the
 * question only the composed page can answer — can a user pick the last
 * activity in the catalogue?
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { CATALOGUE_PAGE_SIZE } from '@/api/paginate';
import { server } from '../mocks/server';
// The one budget for every asynchronous step, checked against the configured
// `testTimeout` in `waitBudget.test.ts` (#1531).
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

/**
 * The page size `listActivities(params?, offset = 0, limit = 50)` applies when a
 * caller passes none, and the same default the backend's shared pagination
 * dependency applies to a request that carries none.
 *
 * It bounds this fixture from below: a catalogue of this size or smaller is
 * returned whole by the capped reader too, and the case would pass against the
 * defect. Measured on the sibling file `FertilizerListPageCatalogueReach` before
 * shrinking one of these fixtures again (#1531): a fixture small enough to be
 * cheap is a fixture that certifies nothing.
 */
const API_DEFAULT_PAGE_SIZE = 50;

/**
 * One row past that bound — deliberately the size of the seeded catalogue, so
 * the fixture is the production situation rather than an exaggerated one.
 */
const CATALOGUE_SIZE = API_DEFAULT_PAGE_SIZE + 1;

/** The row the capped reader never delivered: the last one the server returns. */
const LAST_KEY = `act-${CATALOGUE_SIZE - 1}`;
const LAST_NAME_DE = `Letzte Aktivität ${CATALOGUE_SIZE - 1}`;

function makeActivity(index: number): Activity {
  const isLast = index === CATALOGUE_SIZE - 1;
  return {
    key: `act-${index}`,
    tenant_key: 't',
    name: isLast ? `Last activity ${index}` : `Activity ${index}`,
    name_de: isLast ? LAST_NAME_DE : `Aktivität ${index}`,
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

const CATALOGUE: Activity[] = Array.from({ length: CATALOGUE_SIZE }, (_v, index) =>
  makeActivity(index),
);

/**
 * A catalogue that does not fit in one request, for the loading case below.
 *
 * Bound to the production page size rather than to a literal: `fetchAllPages`
 * asks for `CATALOGUE_PAGE_SIZE` rows and continues only while a *full* page
 * comes back, so the boundary this case is about exists at exactly one size.
 */
const PAGED_CATALOGUE: Activity[] = Array.from(
  { length: CATALOGUE_PAGE_SIZE + 3 },
  (_v, index) => makeActivity(index),
);
const PAGED_LAST_KEY = `act-${PAGED_CATALOGUE.length - 1}`;

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

/**
 * Installs the page's handlers, with an activity endpoint that pages the way the
 * backend does: `offset`/`limit` over a stable order, and the shared
 * pagination dependency's own default when the caller sends no `limit`. A
 * caller that asks for one page therefore learns nothing about the rest.
 *
 * @param activitiesResponder Optional override for the activity endpoint, used
 *   by the loading and failure cases.
 * @returns A recorder of the `(offset, limit)` pairs the page requested.
 */
function serveWorkflow(
  activitiesResponder?: Parameters<typeof http.get>[1],
): { requests: { offset: number; limit: number }[] } {
  const requests: { offset: number; limit: number }[] = [];

  const pagingHandler = ({ request }: { request: Request }) => {
    const url = new URL(request.url);
    const offset = Number(url.searchParams.get('offset') ?? '0');
    const limit = Number(url.searchParams.get('limit') ?? String(API_DEFAULT_PAGE_SIZE));
    requests.push({ offset, limit });
    return HttpResponse.json(CATALOGUE.slice(offset, offset + limit));
  };

  server.use(
    http.get(WF_URL, () => HttpResponse.json(makeWorkflow())),
    http.get(TEMPLATES_URL, () => HttpResponse.json([])),
    http.get(EXECUTIONS_URL, () => HttpResponse.json([])),
    http.get(PHASES_URL, () => HttpResponse.json([])),
    http.get('/api/v1/species', () => HttpResponse.json({ items: [], total: 0 })),
    http.get('/api/v1/t/test-tenant/favorites', () => HttpResponse.json([])),
    http.get(ACTIVITIES_URL, activitiesResponder ?? pagingHandler),
  );
  return { requests };
}

/** Opens the task-template tab and the activity catalogue dialog. */
async function openCatalogueDialog(
  user: ReturnType<typeof userEvent.setup>,
): Promise<HTMLElement> {
  await screen.findByTestId('workflow-detail-page');
  await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
  await user.click(await screen.findByTestId('add-activity-from-catalog-button'));
  const dialogs = await screen.findAllByRole('dialog');
  return dialogs[dialogs.length - 1];
}

describe('WorkflowDetailPage — the activity picker offers the whole catalogue (#1530)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    // Unmount before resetting the language, for the reason given in
    // WorkflowDetailPage.test.tsx: the reset would otherwise re-render every
    // still-mounted useTranslation() consumer outside act().
    cleanup();
    i18n.changeLanguage('en');
  });

  it('offers the activity that sits past the reader default, and finds it by search', async () => {
    const { requests } = serveWorkflow();
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    // The assertion that carries the issue. Against the capped reader this row
    // never reached the component, so the dialog listed 50 of 51 activities and
    // answered every filter over those 50.
    await waitFor(
      () => {
        expect(within(dialog).getByTestId(`activity-row-${LAST_KEY}`)).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );

    // ... and it survives the dialog's own search box, which is the route a user
    // actually takes to a catalogue of this size.
    const search = within(dialog).getByTestId('activity-catalogue-search');
    await user.click(within(search).getByRole('textbox'));
    await user.paste(LAST_NAME_DE);

    await waitFor(
      () => {
        expect(within(dialog).getByTestId(`activity-row-${LAST_KEY}`)).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    // The counterpart the positive assertion needs: a filter that matched
    // everything would satisfy it without the catalogue being complete.
    expect(within(dialog).queryByTestId('activity-row-act-0')).toBeNull();

    // The complete reader asks for more than one default page; the capped one
    // could not have produced the row above with any number of requests.
    expect(requests.length).toBeGreaterThan(0);
    expect(requests.every((request) => request.limit > API_DEFAULT_PAGE_SIZE)).toBe(true);
  });

  it('stays in its loading state across a page boundary, not just the first page', async () => {
    // What makes this worth its own case: `fetchAllPages` is *sequential*, so
    // the dialog is in flight for as long as the whole catalogue takes. If the
    // loading flag were cleared when the first page arrived, the dialog would
    // present a list that is neither complete nor marked as loading — an answer
    // that happens to be wrong, which is the failure mode of the whole class.
    //
    // So the catalogue here is deliberately larger than one request: the first
    // page is served in full (a full page is what tells the loop to continue),
    // and the second is held on a gate. A fixture at or below `PAGE_SIZE` would
    // make this case green whatever the page did after page one, because there
    // would be no page two.
    let releaseSecondPage!: () => void;
    const secondPageArrives = new Promise<void>((resolve) => {
      releaseSecondPage = resolve;
    });
    let resolveFirstPageServed!: () => void;
    const firstPageServed = new Promise<void>((resolve) => {
      resolveFirstPageServed = resolve;
    });

    // Gated rather than delayed: a fixed delay races the clicks that open the
    // dialog, and a race that resolves early turns this into a green run that
    // asserted nothing about the loading state.
    serveWorkflow(async ({ request }) => {
      const url = new URL(request.url);
      const offset = Number(url.searchParams.get('offset') ?? '0');
      const limit = Number(url.searchParams.get('limit') ?? String(API_DEFAULT_PAGE_SIZE));
      if (offset === 0) {
        resolveFirstPageServed();
        return HttpResponse.json(PAGED_CATALOGUE.slice(0, limit));
      }
      await secondPageArrives;
      return HttpResponse.json(PAGED_CATALOGUE.slice(offset, offset + limit));
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);
    await firstPageServed;
    // Let React flush whatever the first page could have triggered, so the
    // assertion below cannot pass merely by running before a re-render.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    // A full first page has arrived and the catalogue is still incomplete:
    // spinner up, nothing offered.
    expect(within(dialog).getByRole('progressbar')).toBeTruthy();
    expect(within(dialog).queryByTestId('activity-row-act-0')).toBeNull();

    releaseSecondPage();

    await waitFor(
      () => {
        expect(within(dialog).getByTestId(`activity-row-${PAGED_LAST_KEY}`)).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(within(dialog).queryByRole('progressbar')).toBeNull();
    // The row that only exists on the second page is the one asserted above, so
    // this case also fails if the loop stops at the page boundary.
    expect(PAGED_CATALOGUE.length).toBeGreaterThan(CATALOGUE_PAGE_SIZE);
  });

  it('reports a failed catalogue load instead of leaving the dialog spinning', async () => {
    // A rejection on any page propagates out of the paging loop; the dialog must
    // leave its loading state and say so, rather than presenting the pages that
    // did arrive as if they were the catalogue.
    serveWorkflow(() => new HttpResponse(null, { status: 500 }));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    await waitFor(
      () => {
        expect(within(dialog).queryByRole('progressbar')).toBeNull();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(within(dialog).queryByTestId('activity-row-act-0')).toBeNull();
    // This used to assert the `errors.server` toast, because a toast was the
    // only thing distinguishing a failed load from an empty catalogue — and it
    // dismisses itself, after which the dialog claimed the catalogue was empty.
    // #1568 moved the distinction into the list, where it persists: the failure
    // now has its own region and its own retry. The toast is gone on purpose,
    // so asserting it here would pin the defect rather than the repair.
    // `WorkflowDetailPageCatalogueState.test.tsx` owns the three-state contract;
    // what this case still guards is the reach half — a rejection anywhere in
    // the paging sequence must not present the pages that did arrive as the
    // catalogue.
    await waitFor(
      () => {
        expect(within(dialog).getByTestId('activity-catalogue-error')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
  });
});
