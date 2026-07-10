import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PhaseDefinition } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

import PhaseDefinitionListPage from '@/pages/phasen/PhaseDefinitionListPage';

const LIST_URL = '/api/v1/phase-definitions';
const DELETE_URL = '/api/v1/phase-definitions/:key';

function makeDefinition(overrides: Partial<PhaseDefinition> = {}): PhaseDefinition {
  return {
    key: 'def-1',
    name: 'vegetative',
    display_name: 'Vegetative',
    display_name_de: 'Vegetativ',
    description: 'Vegetative growth phase.',
    description_de: 'Vegetative Wachstumsphase.',
    typical_duration_days: 28,
    stress_tolerance: 'medium',
    watering_interval_days: 3,
    illustration: '',
    tags: ['indoor'],
    is_system: false,
    usage_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function useDefinitions(rows: PhaseDefinition[]) {
  server.use(http.get(LIST_URL, () => HttpResponse.json(rows)));
}

describe('PhaseDefinitionListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded definition row', async () => {
    useDefinitions([makeDefinition()]);
    renderWithProviders(<PhaseDefinitionListPage />);

    expect(await screen.findByText('Vegetativ')).toBeInTheDocument();
    expect(screen.getByTestId('create-definition-button')).toBeInTheDocument();
  });

  it('renders columns and falls back to name (EN locale)', async () => {
    await i18n.changeLanguage('en');
    useDefinitions([
      makeDefinition({ display_name: '', display_name_de: '', usage_count: 4 }),
    ]);
    renderWithProviders(<PhaseDefinitionListPage />);

    // display_name empty -> falls back to raw name
    expect(await screen.findAllByText('vegetative')).toBeTruthy();
    // usage count column value rendered
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('filters and sorts through the table toolbar', async () => {
    useDefinitions([
      makeDefinition({ key: 'a', name: 'alpha', display_name_de: 'Alpha', typical_duration_days: 5, usage_count: 1 }),
      makeDefinition({ key: 'b', name: 'beta', display_name_de: 'Beta', stress_tolerance: 'low', typical_duration_days: 40, usage_count: 9 }),
    ]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Alpha');
    const searchBox = within(screen.getByTestId('table-search-input')).getByRole('textbox');
    await user.type(searchBox, 'beta');
    await waitFor(
      () => expect(screen.queryByText('Alpha')).not.toBeInTheDocument(),
      { timeout: 3000 },
    );
    expect(screen.getByText('Beta')).toBeInTheDocument();
    await user.clear(searchBox);
    await waitFor(() => expect(screen.getByText('Alpha')).toBeInTheDocument(), { timeout: 3000 });

    const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    for (const label of [
      i18n.t('common.name'),
      i18n.t('pages.phaseSequences.stressTolerance'),
      i18n.t('pages.phaseSequences.typicalDuration'),
      i18n.t('pages.phaseSequences.usageCount'),
    ]) {
      const header = screen.getByRole('columnheader', { name: new RegExp(esc(label)) });
      await user.click(within(header).getByRole('button'));
    }
    expect(screen.getByText('Alpha')).toBeInTheDocument();
  });

  it('renders the mobile card view on a narrow viewport', async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      useDefinitions([makeDefinition()]);
      renderWithProviders(<PhaseDefinitionListPage />);

      expect(await screen.findByTestId('data-table-cards')).toBeInTheDocument();
      expect(screen.getByText('Vegetativ')).toBeInTheDocument();
    } finally {
      window.matchMedia = original;
    }
  });

  it('navigates to the definition detail on row click', async () => {
    useDefinitions([makeDefinition()]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await user.click(await screen.findByText('Vegetativ'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen/def-1');
  });

  it('opens the create dialog from the header action', async () => {
    useDefinitions([makeDefinition()]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getByTestId('create-definition-button'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });

  it('opens the edit dialog from the row action', async () => {
    useDefinitions([makeDefinition()]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getByRole('button', { name: i18n.t('common.edit') }));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });

  it('deletes a definition through the confirm dialog', async () => {
    let deletedKey: string | null = null;
    useDefinitions([makeDefinition()]);
    server.use(
      http.delete(DELETE_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('def-1'));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
    expect(
      await screen.findByText(i18n.t('pages.phaseSequences.definitionDeleted')),
    ).toBeInTheDocument();
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    let resolveDelete: (() => void) | null = null;
    useDefinitions([makeDefinition()]);
    server.use(
      http.delete(
        DELETE_URL,
        () =>
          new Promise<Response>((resolve) => {
            resolveDelete = () => resolve(new HttpResponse(null, { status: 204 }));
          }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toHaveAttribute('aria-busy', 'true'),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete!();
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('surfaces an error when the delete request fails', async () => {
    useDefinitions([makeDefinition()]);
    server.use(
      http.delete(DELETE_URL, () => new HttpResponse(null, { status: 500 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('renders an error state with retry when the list request fails', async () => {
    let calls = 0;
    server.use(
      http.get(LIST_URL, () => {
        calls += 1;
        if (calls === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([makeDefinition()]);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    expect((await screen.findAllByText(i18n.t('errors.server'))).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByText('Vegetativ')).toBeInTheDocument();
  });

  it('opens the create dialog from the empty-state action', async () => {
    useDefinitions([]);
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionListPage />);

    await user.click(
      await screen.findByRole('button', {
        name: i18n.t('pages.phaseSequences.createDefinition'),
      }),
    );
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });

  it('disables the delete action for an in-use definition and hides actions for system data', async () => {
    useDefinitions([
      makeDefinition({ key: 'inuse', name: 'inuse', display_name_de: 'InUse', usage_count: 3 }),
      makeDefinition({ key: 'sys', name: 'sys', display_name_de: 'SystemDef', is_system: true }),
    ]);
    renderWithProviders(<PhaseDefinitionListPage />);

    await screen.findByText('InUse');
    // In-use definition: delete button present but disabled.
    const deleteButtons = screen.getAllByRole('button', { name: i18n.t('common.delete') });
    expect(deleteButtons).toHaveLength(1);
    expect(deleteButtons[0]).toBeDisabled();
    // System definition has neither edit nor delete action.
    expect(screen.getByText('SystemDef')).toBeInTheDocument();
  });
});
