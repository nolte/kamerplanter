import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import type { PhaseHistoryEntry } from '@/api/types';

// PhaseHistoryTable loads and mutates history through the phases endpoint module.
vi.mock('@/api/endpoints/phases', () => ({
  getPhaseHistory: vi.fn(),
  updatePhaseHistoryDates: vi.fn(),
  deletePhaseHistory: vi.fn(),
}));

// Controllable viewport: DataTable switches to its mobile-card renderer when
// useMediaQuery reports a narrow screen. Default is desktop (false).
let isMobileViewport = false;
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => isMobileViewport }));

import PhaseHistoryTable from '@/pages/durchlaeufe/PhaseHistoryTable';
import { getPhaseHistory, updatePhaseHistoryDates, deletePhaseHistory } from '@/api/endpoints/phases';

const mockGet = vi.mocked(getPhaseHistory);
const mockUpdate = vi.mocked(updatePhaseHistoryDates);
const mockDelete = vi.mocked(deletePhaseHistory);

function makeHistory(overrides: Partial<PhaseHistoryEntry> = {}): PhaseHistoryEntry {
  return {
    key: 'h-1',
    phase_name: 'vegetative',
    entered_at: '2024-03-01T10:00:00Z',
    exited_at: '2024-03-15T10:00:00Z',
    actual_duration_days: 14,
    transition_reason: 'manual',
    performance_score: null,
    ...overrides,
  };
}

describe('PhaseHistoryTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isMobileViewport = false;
  });

  it('shows a spinner while the history is loading', () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows the empty state when there is no history', async () => {
    mockGet.mockResolvedValue([]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    expect(await screen.findByText(i18n.t('pages.plantingRuns.noPlantsYet'))).toBeInTheDocument();
  });

  it('falls back to the empty state when loading fails', async () => {
    mockGet.mockRejectedValue(new Error('boom'));
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    expect(await screen.findByText(i18n.t('pages.plantingRuns.noPlantsYet'))).toBeInTheDocument();
  });

  it('renders history rows with duration and reason', async () => {
    mockGet.mockResolvedValue([makeHistory()]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    expect(await screen.findByText('vegetative')).toBeInTheDocument();
    expect(screen.getByText('14d')).toBeInTheDocument();
    expect(screen.getByText('manual')).toBeInTheDocument();
  });

  it('renders em-dashes for missing exit date, duration and reason', async () => {
    mockGet.mockResolvedValue([
      makeHistory({ key: 'h-2', exited_at: null, actual_duration_days: null, transition_reason: '' }),
    ]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    await screen.findByText('vegetative');
    // exit-date cell, duration cell and reason cell all fall back to '—'.
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(3);
  });

  it('saves an edited phase date and notifies the parent', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    mockGet.mockResolvedValue([makeHistory()]);
    mockUpdate.mockResolvedValue(makeHistory());

    renderWithProviders(<PhaseHistoryTable plantKey="p1" onChanged={onChanged} />);
    await screen.findByText('vegetative');

    await user.click(screen.getByTestId('edit-phase-date-h-1'));
    await user.click(screen.getByTestId('save-phase-date-button'));

    await waitFor(() => expect(mockUpdate).toHaveBeenCalled());
    expect(mockUpdate).toHaveBeenCalledWith(
      'p1',
      'h-1',
      expect.objectContaining({ entered_at: expect.any(String), exited_at: expect.any(String) }),
    );
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  it('cancels editing and restores the action buttons', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue([makeHistory()]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    await screen.findByText('vegetative');

    await user.click(screen.getByTestId('edit-phase-date-h-1'));
    expect(screen.getByTestId('save-phase-date-button')).toBeInTheDocument();

    await user.click(screen.getByTestId('cancel-phase-date-button'));
    expect(screen.getByTestId('edit-phase-date-h-1')).toBeInTheDocument();
    expect(screen.queryByTestId('save-phase-date-button')).toBeNull();
  });

  it('handles a save error without crashing', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue([makeHistory()]);
    mockUpdate.mockRejectedValue(new Error('save failed'));

    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    await screen.findByText('vegetative');

    await user.click(screen.getByTestId('edit-phase-date-h-1'));
    await user.click(screen.getByTestId('save-phase-date-button'));

    await waitFor(() => expect(mockUpdate).toHaveBeenCalled());
    // Editor stays open on failure; the table survives the rejected promise.
    expect(screen.getByTestId('save-phase-date-button')).toBeInTheDocument();
  });

  it('deletes a phase after confirmation', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    mockGet.mockResolvedValue([makeHistory()]);
    mockDelete.mockResolvedValue(undefined);

    renderWithProviders(<PhaseHistoryTable plantKey="p1" onChanged={onChanged} />);
    await screen.findByText('vegetative');

    await user.click(screen.getByTestId('delete-phase-h-1'));
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();

    await user.click(screen.getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith('p1', 'h-1'));
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  it('renders mobile cards with duration and reason fields on a narrow viewport', async () => {
    isMobileViewport = true;
    mockGet.mockResolvedValue([makeHistory()]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    // Mobile card renders the phase name plus the optional duration/reason fields.
    expect(await screen.findAllByText('vegetative')).not.toHaveLength(0);
    expect(screen.getByText('14d')).toBeInTheDocument();
    expect(screen.getByText('manual')).toBeInTheDocument();
  });

  it('omits optional fields in the mobile card when data is missing', async () => {
    isMobileViewport = true;
    mockGet.mockResolvedValue([
      makeHistory({ exited_at: null, actual_duration_days: null, transition_reason: '' }),
    ]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    await screen.findAllByText('vegetative');
    // No duration/reason chips when the underlying values are absent.
    expect(screen.queryByText('14d')).toBeNull();
    expect(screen.queryByText('manual')).toBeNull();
  });

  it('closes the delete dialog on cancel without deleting', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue([makeHistory()]);
    renderWithProviders(<PhaseHistoryTable plantKey="p1" />);
    await screen.findByText('vegetative');

    await user.click(screen.getByTestId('delete-phase-h-1'));
    await screen.findByTestId('confirm-dialog');
    await user.click(screen.getByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(mockDelete).not.toHaveBeenCalled();
  });
});
