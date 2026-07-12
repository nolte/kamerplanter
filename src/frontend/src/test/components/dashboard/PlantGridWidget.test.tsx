import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../helpers';
import PlantGridWidget from '@/components/dashboard/widgets/PlantGridWidget';
import type { PlantGridEntry } from '@/components/dashboard/widgets/PlantGridWidget';

// The widget pulls its data from the DashboardDataContext; mock the hook so each
// test drives the render state directly.
const payloadMock = vi.hoisted(() => ({
  useWidgetPayload: vi.fn(() => ({ payload: null as unknown, loading: false })),
}));
vi.mock('@/components/dashboard/DashboardDataContext', () => ({
  useWidgetPayload: payloadMock.useWidgetPayload,
}));

// Deep-link gating (#461) is REQ-042 module-visibility driven; mock it so each
// test controls whether the plant route is visible deterministically.
const moduleVisibilityMock = vi.hoisted(() => ({
  useModuleVisibility: vi.fn((): { isPathVisible: (path: string) => boolean } => ({
    isPathVisible: () => true,
  })),
}));
vi.mock('@/hooks/useModuleVisibility', () => ({
  useModuleVisibility: moduleVisibilityMock.useModuleVisibility,
}));

const PLANTS: PlantGridEntry[] = [
  {
    _key: 'p1',
    plant_name: 'Basilikum',
    species_key: 'ocimum-basilicum',
    cultivar_name: 'Genovese',
    phase_key: 'veg',
    phase_name: 'Vegetativ',
    location_key: 'loc-1',
    location_name: 'Balkon',
    has_open_task: true,
    next_due_date: '2026-07-14T00:00:00+00:00',
  },
  {
    _key: 'p2',
    plant_name: null,
    species_key: 'solanum-lycopersicum',
    cultivar_name: null,
    phase_key: 'flower',
    phase_name: 'Blüte',
    location_key: 'loc-2',
    location_name: 'Gewächshaus',
    has_open_task: false,
    next_due_date: null,
  },
];

function render(editMode = false, route = '/') {
  return renderWithProviders(
    <PlantGridWidget widgetKey="plant_grid" instanceId="inst-1" editMode={editMode} />,
    { route },
  );
}

// This jsdom build ships without a working localStorage; install a minimal
// in-memory stub so the format-persistence path is exercisable (the widget
// itself guards access, so production is unaffected either way).
function installLocalStorageStub() {
  const store = new Map<string, string>();
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  installLocalStorageStub();
  payloadMock.useWidgetPayload.mockReturnValue({ payload: { plants: PLANTS }, loading: false });
  moduleVisibilityMock.useModuleVisibility.mockReturnValue({ isPathVisible: () => true });
});

describe('PlantGridWidget', () => {
  it('renders one card per plant instance with glanceable status', () => {
    render();
    const grid = screen.getByTestId('widget-plant_grid-cards');
    // A card per instance.
    expect(screen.getByTestId('plant-grid-card-p1')).toBeInTheDocument();
    expect(screen.getByTestId('plant-grid-card-p2')).toBeInTheDocument();
    // Detailed format (default) surfaces cultivar, phase, location and next-due.
    const card = screen.getByTestId('plant-grid-card-p1');
    expect(within(card).getByText('Basilikum')).toBeInTheDocument();
    expect(within(card).getByText('Genovese')).toBeInTheDocument();
    expect(within(card).getByText('Vegetativ')).toBeInTheDocument();
    expect(within(card).getByText('Balkon')).toBeInTheDocument();
    // i18n label (tests run under the EN locale).
    expect(within(card).getByText(/Due:/)).toBeInTheDocument();
    // A nameless plant falls back to a humanized species-key label.
    expect(within(grid).getByText('Solanum Lycopersicum')).toBeInTheDocument();
  });

  it('deep-links each card to its plant detail — no nested <a>', () => {
    render();
    const card = screen.getByTestId('plant-grid-card-p1');
    expect(card.tagName).toBe('A');
    expect(card).toHaveAttribute('href', '/pflanzen/plant-instances/p1');
    expect(card.parentElement?.closest('a')).toBeNull();
  });

  it('flags plants with an open task visibly and non-visually', () => {
    render();
    // Visual badge/marker present only on the open-task plant.
    expect(screen.getByTestId('plant-grid-open-task-chip-p1')).toBeInTheDocument();
    expect(screen.queryByTestId('plant-grid-open-task-chip-p2')).not.toBeInTheDocument();
    // Non-visual: the open-task plant's accessible name conveys the flag.
    const card = screen.getByTestId('plant-grid-card-p1');
    expect(card).toHaveAccessibleName(/open task/i);
  });

  it('filters by open-task facet', () => {
    render();
    // Open the task filter and pick "with open task".
    const select = within(screen.getByTestId('column-filter-pg_task')).getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByTestId('column-filter-pg_task-option-open'));
    // Only p1 (has_open_task) remains.
    expect(screen.getByTestId('plant-grid-card-p1')).toBeInTheDocument();
    expect(screen.queryByTestId('plant-grid-card-p2')).not.toBeInTheDocument();
  });

  it('shows a distinct "no matches" state when a filter excludes everything', () => {
    // Both plants lack a phase → filtering to a real phase yields no matches.
    payloadMock.useWidgetPayload.mockReturnValue({
      payload: { plants: [{ ...PLANTS[0], has_open_task: false }] },
      loading: false,
    });
    render();
    const select = within(screen.getByTestId('column-filter-pg_task')).getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByTestId('column-filter-pg_task-option-open'));
    expect(screen.getByTestId('widget-plant_grid-no-matches')).toBeInTheDocument();
  });

  it('switches card format and persists the choice', () => {
    render();
    // Detailed by default: location is shown.
    expect(within(screen.getByTestId('plant-grid-card-p1')).getByText('Balkon')).toBeInTheDocument();
    // Switch to compact → location/next-due are dropped for breadth.
    fireEvent.click(screen.getByTestId('plant-grid-format-compact'));
    expect(within(screen.getByTestId('plant-grid-card-p1')).queryByText('Balkon')).not.toBeInTheDocument();
    // Phase chip (breadth-safe) stays.
    expect(within(screen.getByTestId('plant-grid-card-p1')).getByText('Vegetativ')).toBeInTheDocument();
    // Persisted to localStorage.
    expect(window.localStorage.getItem('kp-plant-grid-format')).toBe('compact');
  });

  it('renders the empty state for a tenant without active plants', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { plants: [] }, loading: false });
    render();
    expect(screen.getByTestId('widget-plant_grid-empty')).toBeInTheDocument();
  });

  it('renders the loading skeleton state', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: true });
    render();
    expect(screen.getByTestId('widget-plant_grid-loading')).toBeInTheDocument();
  });

  it('renders cards inert (no link, no controls) in edit mode', () => {
    render(true);
    const card = screen.getByTestId('plant-grid-card-p1');
    expect(card.tagName).not.toBe('A');
    // Filter bar + format switch are hidden so drag/resize own the pointer.
    expect(screen.queryByTestId('plant-grid-format-switch')).not.toBeInTheDocument();
    expect(screen.queryByTestId('column-filter-bar')).not.toBeInTheDocument();
  });
});
