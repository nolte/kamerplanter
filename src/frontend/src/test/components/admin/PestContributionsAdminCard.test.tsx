import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import { PestContributionsAdminCard } from '@/components/admin/PestContributionsAdminCard';
import { renderWithProviders } from '../../helpers';
import type { Pest, PestContribution, PestContributionList } from '@/api/types';

vi.mock('@/api/endpoints/ipm', () => ({
  listPests: vi.fn(),
}));
import { listPests } from '@/api/endpoints/ipm';

vi.mock('@/api/endpoints/adminPestRecognition', () => ({
  listPestContributions: vi.fn(),
  setPestContributionPromotion: vi.fn(),
}));
import {
  listPestContributions,
  setPestContributionPromotion,
} from '@/api/endpoints/adminPestRecognition';

// AuthImage does an authenticated fetch — stub it to a plain img.
vi.mock('@/components/common/AuthImage', () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} data-testid="pest-contribution-thumb" />,
}));

function pest(overrides: Partial<Pest> = {}): Pest {
  return {
    key: 'p1',
    scientific_name: 'Tetranychus urticae',
    common_name: 'Two-spotted spider mite',
    common_name_de: 'Spinnmilbe',
    pest_type: 'mite',
    lifecycle_days: null,
    optimal_temp_min: null,
    optimal_temp_max: null,
    detection_difficulty: 'medium',
    description: null,
    description_de: null,
    damage_symptoms: null,
    damage_symptoms_de: null,
    affected_plant_parts: [],
    host_plants: [],
    host_plants_de: [],
    prevention_tips: null,
    prevention_tips_de: null,
    monitoring_hints: null,
    monitoring_hints_de: null,
    severity: null,
    optimal_humidity_min: null,
    optimal_humidity_max: null,
    detection_slug: null,
    reference_image_refs: [],
    has_reference_images: false,
    reference_image_count: 0,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function contribution(overrides: Partial<PestContribution> = {}): PestContribution {
  return {
    id: 'c1',
    pest_key: 'p1',
    attachment_id: 'a1',
    content_uri: '/api/v1/ipm/pest-images/c1',
    thumbnail_uri: '/api/v1/ipm/pest-images/c1/thumbnails/512',
    status: 'private',
    caption: 'Webs on leaf underside',
    tenant_key: 't1',
    contributed_by: 'u1',
    created_at: '2026-06-01T10:00:00Z',
    promoted_at: null,
    promoted_by: null,
    ...overrides,
  };
}

function list(images: PestContribution[]): PestContributionList {
  return {
    pest_key: 'p1',
    count: images.length,
    promoted_count: images.filter((i) => i.status === 'promoted').length,
    images,
  };
}

async function selectPest() {
  const input = await screen.findByLabelText('Schädling auswählen');
  await userEvent.click(input);
  await userEvent.click(await screen.findByText('Spinnmilbe'));
}

describe('PestContributionsAdminCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
    vi.mocked(listPests).mockResolvedValue([pest()]);
  });

  it('lists the contributed images for the selected pest', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([contribution({ id: 'c1' }), contribution({ id: 'c2' })]));
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();

    const rows = await screen.findAllByTestId('pest-contribution-row');
    expect(rows).toHaveLength(2);
    expect(listPestContributions).toHaveBeenCalledWith('p1');
  });

  it('shows an empty-state hint when the pest has no contributions', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([]));
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    expect(await screen.findByTestId('pest-contributions-empty')).toBeInTheDocument();
  });

  it('promotes a private contribution and reflects the new global status', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([contribution({ id: 'c1', status: 'private' })]));
    vi.mocked(setPestContributionPromotion).mockResolvedValue({
      id: 'c1',
      pest_key: 'p1',
      status: 'promoted',
      is_active: true,
      promoted_at: '2026-06-21T12:00:00Z',
      promoted_by: 'admin',
    });
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    const row = await screen.findByTestId('pest-contribution-row');
    expect(within(row).getByTestId('pest-contribution-status')).toHaveTextContent('Privat');

    await userEvent.click(within(row).getByTestId('pest-contribution-promote'));

    await waitFor(() => expect(setPestContributionPromotion).toHaveBeenCalledWith('p1', 'c1', true));
    await waitFor(() =>
      expect(screen.getByTestId('pest-contribution-row')).toHaveAttribute('data-status', 'promoted'),
    );
    expect(within(screen.getByTestId('pest-contribution-row')).getByTestId('pest-contribution-status')).toHaveTextContent(
      'Global',
    );
  });

  it('shows a fallback alert when the pest list fails to load', async () => {
    vi.mocked(listPests).mockRejectedValue(new Error('boom'));
    renderWithProviders(<PestContributionsAdminCard />);

    expect(await screen.findByTestId('pest-contributions-pests-unavailable')).toBeInTheDocument();
    // The pest selector is hidden while the list is unavailable.
    expect(screen.queryByTestId('pest-contributions-pest-select')).not.toBeInTheDocument();
  });

  it('shows a fallback alert when contributions fail to load', async () => {
    vi.mocked(listPestContributions).mockRejectedValue(new Error('boom'));
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    expect(await screen.findByTestId('pest-contributions-unavailable')).toBeInTheDocument();
  });

  it('clears the contribution list when the pest selection is cleared', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([contribution({ id: 'c1' })]));
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    expect(await screen.findByTestId('pest-contribution-row')).toBeInTheDocument();

    await userEvent.click(screen.getByLabelText('Clear'));
    await waitFor(() =>
      expect(screen.queryByTestId('pest-contribution-row')).not.toBeInTheDocument(),
    );
  });

  it('closes the demote dialog without calling the API when cancelled', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([contribution({ id: 'c1', status: 'promoted' })]));
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    await userEvent.click(await screen.findByTestId('pest-contribution-promote'));
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('confirm-dialog-cancel'));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument());
    expect(setPestContributionPromotion).not.toHaveBeenCalled();
  });

  it('only updates the promoted contribution and leaves the others untouched', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(
      list([
        contribution({ id: 'c1', status: 'private', caption: 'first' }),
        contribution({ id: 'c2', status: 'private', caption: 'second' }),
      ]),
    );
    vi.mocked(setPestContributionPromotion).mockResolvedValue({
      id: 'c2',
      pest_key: 'p1',
      status: 'promoted',
      is_active: true,
      promoted_at: '2026-06-21T12:00:00Z',
      promoted_by: 'admin',
    });
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    const rows = await screen.findAllByTestId('pest-contribution-row');
    await userEvent.click(within(rows[1]).getByTestId('pest-contribution-promote'));

    await waitFor(() => expect(setPestContributionPromotion).toHaveBeenCalledWith('p1', 'c2', true));
    await waitFor(() => {
      const updated = screen.getAllByTestId('pest-contribution-row');
      expect(updated[0]).toHaveAttribute('data-status', 'private');
      expect(updated[1]).toHaveAttribute('data-status', 'promoted');
    });
  });

  it('renders contributions without caption and thumbnail using fallbacks', async () => {
    vi.mocked(listPests).mockResolvedValue([
      pest({ common_name_de: null, common_name: 'Spider mite fallback' }),
    ]);
    vi.mocked(listPestContributions).mockResolvedValue(
      list([contribution({ id: 'c1', caption: null, thumbnail_uri: null })]),
    );
    renderWithProviders(<PestContributionsAdminCard />);

    const input = await screen.findByLabelText('Schädling auswählen');
    await userEvent.click(input);
    await userEvent.click(await screen.findByText('Spider mite fallback'));

    expect(await screen.findByTestId('pest-contribution-row')).toBeInTheDocument();
  });

  it('requires confirmation before demoting a promoted contribution', async () => {
    vi.mocked(listPestContributions).mockResolvedValue(list([contribution({ id: 'c1', status: 'promoted' })]));
    vi.mocked(setPestContributionPromotion).mockResolvedValue({
      id: 'c1',
      pest_key: 'p1',
      status: 'private',
      is_active: true,
      promoted_at: null,
      promoted_by: null,
    });
    renderWithProviders(<PestContributionsAdminCard />);

    await selectPest();
    const promoteToggle = await screen.findByTestId('pest-contribution-promote');

    // Demote opens a confirmation dialog first — it must NOT call the API immediately.
    await userEvent.click(promoteToggle);
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    expect(setPestContributionPromotion).not.toHaveBeenCalled();

    await userEvent.click(screen.getByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(setPestContributionPromotion).toHaveBeenCalledWith('p1', 'c1', false));
    await waitFor(() =>
      expect(screen.getByTestId('pest-contribution-row')).toHaveAttribute('data-status', 'private'),
    );
  });
});
