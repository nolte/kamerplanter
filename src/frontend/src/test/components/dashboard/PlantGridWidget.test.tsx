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
    instance_id: '7432',
    plant_name: 'Basilikum',
    species_key: 'ocimum-basilicum',
    species_common_name: 'Basil',
    species_scientific_name: 'Ocimum basilicum',
    cultivar_name: 'Genovese',
    phase_key: 'veg',
    phase_definition_key: 'phase-veg',
    phase_name: 'Vegetativ',
    location_key: 'loc-1',
    location_name: 'Balkon',
    has_open_task: true,
    next_due_date: '2026-07-14T00:00:00+00:00',
  },
  {
    _key: 'p2',
    instance_id: '9001',
    // No user label → title falls back to the species common name (R1/A1).
    plant_name: null,
    species_key: 'solanum-lycopersicum',
    species_common_name: 'Tomato',
    species_scientific_name: 'Solanum lycopersicum',
    cultivar_name: null,
    phase_key: 'flower',
    // No resolvable phase definition → phase chip renders without a link (R5).
    phase_definition_key: null,
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
    // A nameless plant falls back to the species common name as its title (R1/A1).
    expect(within(grid).getByText('Tomato')).toBeInTheDocument();
  });

  it('gives each card field its own link and never nests anchors (R4/R6)', () => {
    render();
    const card = screen.getByTestId('plant-grid-card-p1');
    // The card itself is no longer a single card-wide anchor.
    expect(card.tagName).not.toBe('A');
    // Each piece of information is its own link to the matching detail page.
    expect(screen.getByTestId('plant-grid-title-link-p1')).toHaveAttribute(
      'href',
      '/pflanzen/plant-instances/p1',
    );
    expect(screen.getByTestId('plant-grid-species-link-p1')).toHaveAttribute(
      'href',
      '/stammdaten/species/ocimum-basilicum',
    );
    expect(screen.getByTestId('plant-grid-location-link-p1')).toHaveAttribute(
      'href',
      '/standorte/locations/loc-1',
    );
    expect(screen.getByTestId('plant-grid-phase-link-p1')).toHaveAttribute(
      'href',
      '/phasen/definitionen/phase-veg',
    );
    // No anchor is ever nested inside another anchor (valid HTML, R6).
    card.querySelectorAll('a').forEach((anchor) => {
      expect(anchor.parentElement?.closest('a')).toBeNull();
    });
    // R5 graceful degradation: p2 has no resolvable phase definition → its phase
    // chip renders without a link.
    expect(screen.queryByTestId('plant-grid-phase-link-p2')).not.toBeInTheDocument();
    expect(within(screen.getByTestId('plant-grid-card-p2')).getByText('Blüte')).toBeInTheDocument();
  });

  it('shows title falling back to species name when plant_name equals instance_id (R1/A1)', () => {
    // p3: plant_name === instance_id (a bare number, not a real label) → should fall back.
    const p3: PlantGridEntry = {
      _key: 'p3',
      instance_id: '5555',
      plant_name: '5555', // Equals instance_id → not a real user label
      species_key: 'mentha-piperita',
      species_common_name: 'Peppermint',
      species_scientific_name: 'Mentha piperita',
      cultivar_name: null,
      phase_key: 'veg',
      phase_definition_key: 'phase-veg',
      phase_name: 'Vegetativ',
      location_key: 'loc-3',
      location_name: 'Fensterbank',
      has_open_task: false,
      next_due_date: null,
    };
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { plants: [p3] }, loading: false });
    render();
    const card = screen.getByTestId('plant-grid-card-p3');
    // Title should be "Peppermint", not "5555".
    expect(within(card).getByText('Peppermint')).toBeInTheDocument();
    // The bare number should appear as a small reference below the title (detailed format).
    // In EN locale the label is "No. 5555".
    expect(within(card).getByText(/No\. 5555/)).toBeInTheDocument();
  });

  it('shows location in both detailed and compact formats (R3)', () => {
    render();
    // Detailed: location is visible.
    const cardDetailed = screen.getByTestId('plant-grid-card-p1');
    expect(within(cardDetailed).getByText('Balkon')).toBeInTheDocument();
    // Switch to compact format.
    fireEvent.click(screen.getByTestId('plant-grid-format-compact'));
    // Compact: location is still visible (R3, both formats must show it).
    const cardCompact = screen.getByTestId('plant-grid-card-p1');
    expect(within(cardCompact).getByText('Balkon')).toBeInTheDocument();
  });

  it('hides links when isPathVisible returns false per module (REQ-042 gating)', () => {
    // Mock isPathVisible to hide plant-instances route.
    moduleVisibilityMock.useModuleVisibility.mockReturnValue({
      isPathVisible: (path: string) => path !== '/pflanzen/plant-instances',
    });
    render();
    // The title link is hidden (path is not visible).
    expect(screen.queryByTestId('plant-grid-title-link-p1')).not.toBeInTheDocument();
    // The title should still appear as plain text, not a link.
    expect(screen.getByText('Basilikum')).toBeInTheDocument();
    // Other links (species, location, phase) are still visible because those paths pass the gate.
    expect(screen.getByTestId('plant-grid-species-link-p1')).toBeInTheDocument();
    expect(screen.getByTestId('plant-grid-location-link-p1')).toBeInTheDocument();
    expect(screen.getByTestId('plant-grid-phase-link-p1')).toBeInTheDocument();
  });

  it('flags plants with an open task visibly and non-visually', () => {
    render();
    // Visual badge/marker present only on the open-task plant.
    expect(screen.getByTestId('plant-grid-open-task-chip-p1')).toBeInTheDocument();
    expect(screen.queryByTestId('plant-grid-open-task-chip-p2')).not.toBeInTheDocument();
    // Non-visual: the open-task plant carries a readable text badge (not colour-only).
    const card = screen.getByTestId('plant-grid-card-p1');
    expect(within(card).getByText('Open task')).toBeInTheDocument();
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
    // Detailed by default: location and next-due are shown.
    expect(within(screen.getByTestId('plant-grid-card-p1')).getByText('Balkon')).toBeInTheDocument();
    expect(within(screen.getByTestId('plant-grid-card-p1')).getByText(/Due:/)).toBeInTheDocument();
    // Switch to compact → the location stays (R3, shown in both formats) while the
    // next-due line is dropped for breadth.
    fireEvent.click(screen.getByTestId('plant-grid-format-compact'));
    expect(within(screen.getByTestId('plant-grid-card-p1')).getByText('Balkon')).toBeInTheDocument();
    expect(within(screen.getByTestId('plant-grid-card-p1')).queryByText(/Due:/)).not.toBeInTheDocument();
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
