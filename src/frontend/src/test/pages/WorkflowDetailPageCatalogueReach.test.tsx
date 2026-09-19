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
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
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

/**
 * Budget for the page's asynchronous steps — see `WAIT_BUDGET` in the sibling
 * file `FertilizerListPageCatalogueReach.test.tsx` (#1531) for the measurement
 * behind the number, and for why two of them in sequence must still fit inside
 * the 30 s `testTimeout`.
 */
const WAIT_BUDGET = 12000;

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

  it('keeps the dialog in its loading state until the catalogue has arrived', async () => {
    // Paging is sequential, so the dialog is in flight for as long as the whole
    // catalogue takes — not just its first page. The spinner has to cover that
    // window, otherwise the dialog shows an empty list that looks like an answer.
    // Held open by a gate rather than a delay: a fixed delay races the clicks
    // that open the dialog, and a race that resolves early turns this case into
    // a green run that asserted nothing about the loading state.
    let releaseCatalogue!: () => void;
    const catalogueArrives = new Promise<void>((resolve) => {
      releaseCatalogue = resolve;
    });
    serveWorkflow(async () => {
      await catalogueArrives;
      return HttpResponse.json(CATALOGUE);
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    const dialog = await openCatalogueDialog(user);

    expect(within(dialog).getByRole('progressbar')).toBeTruthy();
    expect(within(dialog).queryByTestId('activity-row-act-0')).toBeNull();

    releaseCatalogue();

    await waitFor(
      () => {
        expect(within(dialog).getByTestId(`activity-row-${LAST_KEY}`)).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(within(dialog).queryByRole('progressbar')).toBeNull();
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
    // The toast the 500 produces, asserted by its text: notistack renders the
    // message, and a role-based assertion would pass on any alert the page
    // happens to carry.
    await waitFor(
      () => {
        expect(screen.getAllByText(i18n.t('errors.server')).length).toBeGreaterThan(0);
      },
      { timeout: WAIT_BUDGET },
    );
  });
});
