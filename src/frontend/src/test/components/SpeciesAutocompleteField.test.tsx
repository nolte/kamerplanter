import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import SpeciesAutocompleteField from '@/components/form/SpeciesAutocompleteField';
import type { Species } from '@/api/types';
import { renderWithProviders } from '../helpers';

const species: Species[] = [
  {
    key: 'sp-monstera',
    scientific_name: 'Monstera deliciosa',
    common_names: ['Fensterblatt'],
    genus: 'Monstera',
    family_name: 'Araceae',
  } as unknown as Species,
  {
    key: 'sp-basil',
    scientific_name: 'Ocimum basilicum',
    common_names: [],
    genus: 'Ocimum',
    family_name: 'Lamiaceae',
  } as unknown as Species,
];

function TestForm({ defaultValue = '' }: { defaultValue?: string }) {
  const { control } = useForm({ defaultValues: { species_key: defaultValue } });
  return (
    <SpeciesAutocompleteField
      name="species_key"
      control={control}
      label="Art"
      species={species}
    />
  );
}

describe('SpeciesAutocompleteField', () => {
  it('renders the labelled autocomplete input', () => {
    renderWithProviders(<TestForm />);
    expect(screen.getByLabelText(/art/i)).toBeTruthy();
  });

  it('shows the display label for a preselected species', () => {
    renderWithProviders(<TestForm defaultValue="sp-monstera" />);
    const input = screen.getByLabelText(/art/i) as HTMLInputElement;
    expect(input.value).toBe('Fensterblatt (Monstera deliciosa)');
  });

  it('falls back to the scientific name when no common name exists', () => {
    renderWithProviders(<TestForm defaultValue="sp-basil" />);
    const input = screen.getByLabelText(/art/i) as HTMLInputElement;
    expect(input.value).toBe('Ocimum basilicum');
  });

  it('lists options sorted by display label when opened', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText(/art/i));
    const listbox = screen.getByRole('listbox');
    const options = within(listbox).getAllByRole('option');
    expect(options.length).toBe(2);
  });

  it('selects an option and updates the displayed value', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const input = screen.getByLabelText(/art/i);
    await user.click(input);
    await user.click(screen.getByRole('option', { name: /Fensterblatt/i }));
    expect((input as HTMLInputElement).value).toBe('Fensterblatt (Monstera deliciosa)');
  });

  it('filters options by typing a common name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const input = screen.getByLabelText(/art/i);
    await user.click(input);
    await user.type(input, 'Fenster');
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getAllByRole('option').length).toBe(1);
  });
});
