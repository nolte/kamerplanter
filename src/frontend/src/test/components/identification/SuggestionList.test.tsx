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
});
