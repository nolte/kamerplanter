import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Activity } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'act-1' }),
    useNavigate: () => navigate,
  };
});

const getActivity = vi.fn();
const updateActivity = vi.fn();
const deleteActivity = vi.fn();
vi.mock('@/api/endpoints/activities', () => ({
  getActivity: (...args: unknown[]) => getActivity(...args),
  updateActivity: (...args: unknown[]) => updateActivity(...args),
  deleteActivity: (...args: unknown[]) => deleteActivity(...args),
}));

import ActivityDetailPage from '@/pages/stammdaten/ActivityDetailPage';
import { renderWithProviders } from '../helpers';

function makeActivity(overrides: Partial<Activity> = {}): Activity {
  return {
    key: 'act-1',
    tenant_key: 'tenant-1',
    name: 'Topping',
    name_de: 'Entspitzen',
    description: 'Remove the apical tip.',
    description_de: 'Apikale Spitze entfernen.',
    category: 'training_hst',
    stress_level: 'medium',
    skill_level: 'intermediate',
    recovery_days_default: 3,
    recovery_days_by_species: {},
    forbidden_phases: [],
    restricted_sub_phases: [],
    tools_required: [],
    estimated_duration_minutes: 10,
    requires_photo: false,
    species_compatible: [],
    is_system: false,
    sort_order: 0,
    tags: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/** A deferred promise whose resolution/rejection the test controls. */
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('ActivityDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    getActivity.mockReset().mockResolvedValue(makeActivity());
    updateActivity.mockReset().mockResolvedValue(makeActivity());
    deleteActivity.mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded activity with its German display name', async () => {
    renderWithProviders(<ActivityDetailPage />);
    expect(await screen.findByTestId('activity-detail-page')).toBeInTheDocument();
    // German display name (name_de) is shown in the page title.
    expect(screen.getByText('Entspitzen')).toBeInTheDocument();
  });

  it('shows a loading skeleton while the activity is being fetched', () => {
    // Never-resolving promise keeps the page in its loading state.
    getActivity.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ActivityDetailPage />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('activity-detail-page')).toBeNull();
  });

  it('renders an error display when the fetch fails', async () => {
    getActivity.mockRejectedValue(new Error('boom'));
    renderWithProviders(<ActivityDetailPage />);
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
  });

  it('falls back to the English name when the German name is empty', async () => {
    getActivity.mockResolvedValue(makeActivity({ name_de: '' }));
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');
    // German locale, but name_de is empty -> falls back to activity.name.
    expect(screen.getAllByText('Topping').length).toBeGreaterThan(0);
  });

  it('uses the English name as the display name in the English locale', async () => {
    i18n.changeLanguage('en');
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');
    expect(screen.getByText('Topping')).toBeInTheDocument();
  });

  it('shows the universal-scope alert when no species are restricted', async () => {
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');
    expect(
      screen.getByText(i18n.t('pages.activities.scopeUniversalInfo')),
    ).toBeInTheDocument();
  });

  it('shows the restricted-scope alert when species are compatible', async () => {
    getActivity.mockResolvedValue(makeActivity({ species_compatible: ['sp-1', 'sp-2'] }));
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');
    expect(
      screen.getByText(i18n.t('pages.activities.scopeRestrictedInfo', { count: 2 })),
    ).toBeInTheDocument();
  });

  it('saves edits through the update endpoint once the form is dirty', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');

    // Editing the pre-filled name field makes the form dirty and enables submit.
    const nameField = screen.getByDisplayValue('Topping');
    await user.type(nameField, ' HST');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() =>
      expect(updateActivity).toHaveBeenCalledWith(
        'act-1',
        expect.objectContaining({ name: 'Topping HST' }),
      ),
    );
  });

  it('keeps the page mounted when saving fails', async () => {
    updateActivity.mockRejectedValue(new Error('save failed'));
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');

    const nameField = screen.getByDisplayValue('Topping');
    await user.type(nameField, ' HST');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateActivity).toHaveBeenCalled());
    expect(screen.getByTestId('activity-detail-page')).toBeInTheDocument();
  });

  it('navigates to the list when the form is cancelled', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);
    await screen.findByTestId('activity-detail-page');

    await user.click(screen.getByTestId('form-cancel-button'));
    expect(navigate).toHaveBeenCalledWith('/stammdaten/activities');
  });
});

describe('ActivityDetailPage — delete flow', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    getActivity.mockReset().mockResolvedValue(makeActivity());
    updateActivity.mockReset().mockResolvedValue(makeActivity());
    deleteActivity.mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('deletes the activity through the confirm dialog and navigates back to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);

    await screen.findByTestId('activity-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteActivity).toHaveBeenCalledWith('act-1'));
    expect(navigate).toHaveBeenCalledWith('/stammdaten/activities');
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    const gate = deferred<void>();
    deleteActivity.mockReturnValue(gate.promise);
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);

    await screen.findByTestId('activity-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // The confirm button is busy and the live region announces the pending state.
    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled(),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    gate.resolve();
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/stammdaten/activities'));
  });

  it('cancels the deletion without calling the delete endpoint', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);

    await screen.findByTestId('activity-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(deleteActivity).not.toHaveBeenCalled();
  });

  it('does not navigate when the delete request fails', async () => {
    deleteActivity.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<ActivityDetailPage />);

    await screen.findByTestId('activity-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteActivity).toHaveBeenCalledWith('act-1'));
    expect(navigate).not.toHaveBeenCalled();
  });

  it('hides the delete action for system activities', async () => {
    getActivity.mockResolvedValue(makeActivity({ is_system: true }));
    renderWithProviders(<ActivityDetailPage />);

    await screen.findByTestId('activity-detail-page');
    expect(screen.queryByRole('button', { name: i18n.t('common.delete') })).toBeNull();
  });
});
