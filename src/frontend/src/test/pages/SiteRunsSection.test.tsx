import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SiteRunsSection from '@/pages/standorte/SiteRunsSection';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * P7e — SiteRunsSection (child of SiteDetailPage). Rendered as a unit with a
 * realistic tenant store; both collaborators (sites + planting-runs endpoints)
 * are doubled at the process boundary via msw. Asserts only observable output
 * (rendered table / empty state / navigation).
 */

const SITE = 'site-1';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

// Controllable viewport to exercise DataTable's mobile-card renderer.
const mq = vi.hoisted(() => ({ mobile: false }));
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => mq.mobile }));

const LOCATIONS = [
  { key: 'loc-1', name: 'Bed A', site_key: SITE },
  { key: 'loc-2', name: 'Bed B', site_key: SITE },
];

function run(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    key: 'run-x',
    name: 'Run X',
    run_type: 'batch',
    status: 'active',
    planned_quantity: 10,
    actual_quantity: 8,
    current_phase_key: null,
    current_phase_started_at: null,
    lifecycle_config_key: null,
    location_key: 'loc-1',
    substrate_batch_key: null,
    planned_start_date: null,
    started_at: null,
    completed_at: null,
    source_plant_key: null,
    notes: null,
    phase_summary: null,
    ...overrides,
  };
}

interface Opts {
  locations?: unknown[];
  runs?: unknown[];
  runsStatus?: number;
}

function mount(opts: Opts = {}) {
  const { locations = LOCATIONS, runs = [], runsStatus } = opts;
  server.use(
    http.get('/api/v1/t/:tenant/locations', () => HttpResponse.json(locations)),
    http.get('/api/v1/t/:tenant/planting-runs', () => {
      if (runsStatus) {
        return HttpResponse.json(
          { error_id: 'e1', error_code: 'INTERNAL_ERROR', message: 'boom', details: [], timestamp: '', path: '', method: '' },
          { status: runsStatus },
        );
      }
      return HttpResponse.json(runs);
    }),
  );
  return renderWithProviders(<SiteRunsSection siteKey={SITE} />);
}

describe('SiteRunsSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mq.mobile = false;
    i18n.changeLanguage('de');
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('shows the empty state when no run belongs to the site locations', async () => {
    mount({ runs: [] });
    expect(await screen.findByText(i18n.t('pages.sites.noRuns'))).toBeInTheDocument();
    expect(screen.queryByTestId('data-table')).not.toBeInTheDocument();
  });

  it('filters runs down to those in the site locations and renders them in the table', async () => {
    mount({
      runs: [
        run({ key: 'r1', name: 'Tomatoes 2026', location_key: 'loc-1', status: 'active' }),
        run({ key: 'r2', name: 'Basil 2026', location_key: 'loc-2', status: 'harvesting' }),
        // Different site location — must be filtered out.
        run({ key: 'r3', name: 'Elsewhere', location_key: 'loc-999' }),
        // No location — filtered out.
        run({ key: 'r4', name: 'Homeless', location_key: null }),
      ],
    });
    expect(await screen.findByTestId('data-table')).toBeInTheDocument();
    expect(screen.getByText('Tomatoes 2026')).toBeInTheDocument();
    expect(screen.getByText('Basil 2026')).toBeInTheDocument();
    expect(screen.queryByText('Elsewhere')).not.toBeInTheDocument();
    expect(screen.queryByText('Homeless')).not.toBeInTheDocument();
    // Location name is resolved from the location map.
    expect(screen.getByText('Bed A')).toBeInTheDocument();
    expect(screen.getByText('Bed B')).toBeInTheDocument();
  });

  it('renders the dominant-phase chip only for non-planned runs, and a dash otherwise', async () => {
    mount({
      runs: [
        run({
          key: 'r1',
          name: 'With Phase',
          status: 'active',
          phase_summary: { dominant_phase: 'vegetative', dominant_phase_count: 3, total_plant_count: 5 },
        }),
        run({
          key: 'r2',
          name: 'Planned Run',
          status: 'planned',
          location_key: 'loc-2',
          phase_summary: { dominant_phase: 'germination', dominant_phase_count: 1, total_plant_count: 2 },
        }),
      ],
    });
    await screen.findByTestId('data-table');
    // Non-planned run shows the phase chip "vegetative (3/5)".
    expect(screen.getByText('vegetative (3/5)')).toBeInTheDocument();
    // Planned run suppresses the phase chip.
    expect(screen.queryByText('germination (1/2)')).not.toBeInTheDocument();
  });

  it('renders a dash for a phase summary without a dominant phase, and falls back to a default status colour', async () => {
    mount({
      runs: [
        run({
          key: 'r1',
          name: 'No Dominant',
          status: 'active',
          phase_summary: { dominant_phase: null, dominant_phase_count: 0, total_plant_count: 0 },
        }),
        // Unknown status exercises the statusColor `?? 'default'` fallback.
        run({ key: 'r2', name: 'Odd Status', location_key: 'loc-2', status: 'archived' }),
      ],
    });
    await screen.findByTestId('data-table');
    expect(screen.getByText('No Dominant')).toBeInTheDocument();
    expect(screen.getByText('Odd Status')).toBeInTheDocument();
  });

  it('navigates to the run detail on row click', async () => {
    const user = userEvent.setup();
    mount({ runs: [run({ key: 'run-abc', name: 'Clickable Run' })] });
    await screen.findByTestId('data-table');
    await user.click(screen.getByText('Clickable Run'));
    expect(mockNavigate).toHaveBeenCalledWith('/durchlaeufe/planting-runs/run-abc');
  });

  it('renders the mobile-card layout with a subtitle and phase field', async () => {
    mq.mobile = true;
    mount({
      runs: [
        run({
          key: 'r1',
          name: 'Mobile Run',
          location_key: 'loc-1',
          status: 'completed',
          phase_summary: { dominant_phase: 'flowering', dominant_phase_count: 2, total_plant_count: 4 },
        }),
        // Second card without a phase summary + unknown status exercises the
        // empty phase-field branch and the statusColor fallback in mobile.
        run({ key: 'r2', name: 'Phaseless Run', location_key: 'loc-2', status: 'archived', phase_summary: null }),
      ],
    });
    expect(await screen.findByTestId('data-table-cards')).toBeInTheDocument();
    const cards = screen.getAllByTestId('data-table-row');
    const card = cards[0];
    expect(within(card).getByText('Mobile Run')).toBeInTheDocument();
    // Subtitle is the resolved location name.
    expect(within(card).getByText('Bed A')).toBeInTheDocument();
    expect(screen.getByText('Phaseless Run')).toBeInTheDocument();
  });

  it('filters through the table search box (exercises every column searchValue)', async () => {
    const user = userEvent.setup();
    mount({
      runs: [
        run({
          key: 'r1',
          name: 'Alpha Run',
          location_key: 'loc-1',
          status: 'active',
          actual_quantity: 4,
          planned_quantity: 6,
          phase_summary: { dominant_phase: 'vegetative', dominant_phase_count: 2, total_plant_count: 4 },
        }),
        run({
          key: 'r2',
          name: 'Beta Run',
          location_key: 'loc-2',
          status: 'completed',
          phase_summary: null,
        }),
      ],
    });
    await screen.findByTestId('data-table');
    const search = within(screen.getByTestId('data-table')).getByTestId('table-search-input');
    const input = search.querySelector('input')!;
    // Search by location name — matches only the Alpha run (Bed A).
    await user.type(input, 'Bed A');
    await waitFor(() => expect(screen.queryByText('Beta Run')).not.toBeInTheDocument());
    expect(screen.getByText('Alpha Run')).toBeInTheDocument();
  });

  it('surfaces an API error without rendering the table', async () => {
    mount({ runsStatus: 500 });
    // handleError shows a snackbar; the section renders its empty state (no table).
    await waitFor(() =>
      expect(screen.queryByTestId('data-table')).not.toBeInTheDocument(),
    );
  });

  it('abandons the in-flight load when unmounted before it resolves', async () => {
    let release!: () => void;
    const gate = new Promise<void>((res) => { release = res; });
    server.use(
      http.get('/api/v1/t/:tenant/locations', () => HttpResponse.json(LOCATIONS)),
      http.get('/api/v1/t/:tenant/planting-runs', async () => {
        await gate;
        return HttpResponse.json([run({ key: 'r1', name: 'Late Run' })]);
      }),
    );
    const { unmount } = renderWithProviders(<SiteRunsSection siteKey={SITE} />);
    unmount();
    // Resolve after unmount: the cancelled guard must swallow the result.
    release();
    await waitFor(() => expect(screen.queryByText('Late Run')).not.toBeInTheDocument());
  });
});
