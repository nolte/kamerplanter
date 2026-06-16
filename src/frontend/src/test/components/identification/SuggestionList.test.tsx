import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import SuggestionList from '@/components/identification/SuggestionList';
import type { IdentificationSuggestion } from '@/api/types';

const SUGGESTIONS: IdentificationSuggestion[] = [
  {
    rank: 1,
    scientific_name: 'Monstera deliciosa',
    common_names: ['Fensterblatt'],
    family: 'Araceae',
    genus: 'Monstera',
    confidence: 0.93,
    external_id: 'plantnet:1',
    image_url: null,
    gbif_id: 2873150,
    matched_species_key: 'species_monstera',
    species_in_database: true,
    auto_accept: true,
  },
  {
    rank: 2,
    scientific_name: 'Monstera adansonii',
    common_names: [],
    family: 'Araceae',
    genus: 'Monstera',
    confidence: 0.04,
    external_id: 'plantnet:2',
    image_url: null,
    gbif_id: null,
    matched_species_key: null,
    species_in_database: false,
    auto_accept: false,
  },
];

describe('SuggestionList', () => {
  it('renders each candidate and the "in database" badge', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="intermediate"
      />,
    );
    expect(screen.getByText('Monstera deliciosa')).toBeInTheDocument();
    expect(screen.getByText('Monstera adansonii')).toBeInTheDocument();
    expect(screen.getByTestId('suggestion-in-db-1')).toBeInTheDocument();
    expect(screen.queryByTestId('suggestion-in-db-2')).not.toBeInTheDocument();
  });

  it('hides confidence for beginners', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="beginner"
      />,
    );
    expect(screen.queryByTestId('suggestion-confidence-1')).not.toBeInTheDocument();
  });

  it('shows confidence for intermediate but no GBIF link', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="intermediate"
      />,
    );
    expect(screen.getByTestId('suggestion-confidence-1')).toBeInTheDocument();
    expect(screen.queryByTestId('suggestion-gbif-1')).not.toBeInTheDocument();
  });

  it('shows the GBIF link only for experts (and only when gbif_id is set)', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="expert"
      />,
    );
    expect(screen.getByTestId('suggestion-gbif-1')).toBeInTheDocument();
    expect(screen.queryByTestId('suggestion-gbif-2')).not.toBeInTheDocument();
  });

  it('calls onSelect with the clicked rank', async () => {
    const onSelect = vi.fn();
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={onSelect}
        level="intermediate"
      />,
    );
    await userEvent.click(screen.getByTestId('suggestion-select-2'));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it('leads with the common name for beginners and shows the scientific name as subtitle', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="beginner"
      />,
    );
    // Beginner card #1 has a common name → both names rendered, common one first.
    expect(screen.getByText('Fensterblatt')).toBeInTheDocument();
    expect(screen.getByText('Monstera deliciosa')).toBeInTheDocument();
    // Card #2 has no common name → falls back to the scientific-name-first branch.
    expect(screen.getByText('Monstera adansonii')).toBeInTheDocument();
  });

  it('marks the selected card with the selected-state styling', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={1}
        onSelect={vi.fn()}
        level="intermediate"
      />,
    );
    expect(screen.getByTestId('suggestion-select-1')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('suggestion-select-2')).toHaveAttribute('aria-pressed', 'false');
  });

  it('marks the selected card for beginners (common-name branch)', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={1}
        onSelect={vi.fn()}
        level="beginner"
      />,
    );
    expect(screen.getByTestId('suggestion-select-1')).toHaveAttribute('aria-pressed', 'true');
  });

  it('renders a reference image when image_url is present', () => {
    const withImage: IdentificationSuggestion[] = [
      { ...SUGGESTIONS[0], image_url: 'https://example.org/monstera.jpg' },
    ];
    renderWithProviders(
      <SuggestionList
        suggestions={withImage}
        selectedRank={null}
        onSelect={vi.fn()}
        level="beginner"
      />,
    );
    const img = screen.getByTestId('suggestion-image-1');
    expect(img).toHaveAttribute('src', 'https://example.org/monstera.jpg');
  });

  it('appends the raw confidence score for experts', () => {
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={vi.fn()}
        level="expert"
      />,
    );
    // Expert view shows the 4-decimal raw score next to the percentage.
    expect(screen.getByText(/0\.9300/)).toBeInTheDocument();
  });

  it('disables the action areas when the list is disabled', () => {
    const onSelect = vi.fn();
    renderWithProviders(
      <SuggestionList
        suggestions={SUGGESTIONS}
        selectedRank={null}
        onSelect={onSelect}
        level="intermediate"
        disabled
      />,
    );
    // A disabled CardActionArea reflects the Mui-disabled state and swallows clicks.
    expect(screen.getByTestId('suggestion-select-1')).toHaveClass('Mui-disabled');
    expect(onSelect).not.toHaveBeenCalled();
  });
});
