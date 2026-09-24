import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import SpeciesMultiAutocompleteField from '@/components/form/SpeciesMultiAutocompleteField';
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

function TestForm({
  defaultValue = [],
  disabled,
}: {
  defaultValue?: string[];
  disabled?: boolean;
}) {
  const { control } = useForm({ defaultValues: { species_keys: defaultValue } });
  return (
    <SpeciesMultiAutocompleteField
      name="species_keys"
      control={control}
      label="Arten"
      species={species}
      disabled={disabled}
    />
  );
}

describe('SpeciesMultiAutocompleteField', () => {
  it('renders the labelled multi-select input', () => {
    renderWithProviders(<TestForm />);
    expect(screen.getByLabelText(/arten/i)).toBeTruthy();
  });

  it('shows a chip for each preselected species by display label', () => {
    renderWithProviders(<TestForm defaultValue={['sp-monstera', 'sp-basil']} />);
    expect(screen.getByText('Fensterblatt (Monstera deliciosa)')).toBeInTheDocument();
    expect(screen.getByText('Ocimum basilicum')).toBeInTheDocument();
  });

  it('keeps a stored key the catalogue does not (yet) hold as a chip showing the raw key', () => {
    renderWithProviders(<TestForm defaultValue={['unknown-species']} />);
    expect(screen.getByText('unknown-species')).toBeInTheDocument();
  });

  it('lists options sorted by display label when opened', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText(/arten/i));
    const listbox = screen.getByRole('listbox');
    const options = within(listbox).getAllByRole('option');
    expect(options.map((o) => o.textContent)).toEqual([
      'Fensterblatt (Monstera deliciosa)',
      'Ocimum basilicum',
    ]);
  });

  it('filters options by typing a common name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const input = screen.getByLabelText(/arten/i);
    await user.click(input);
    await user.type(input, 'Fenster');
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getAllByRole('option').length).toBe(1);
  });

  it('adds a species as a chip when picked from the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const input = screen.getByLabelText(/arten/i);
    await user.click(input);
    await user.click(screen.getByRole('option', { name: /Fensterblatt/i }));
    expect(screen.getByText('Fensterblatt (Monstera deliciosa)')).toBeInTheDocument();
  });

  it('excludes an already-selected species from the option list (filterSelectedOptions)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm defaultValue={['sp-monstera']} />);
    await user.click(screen.getByLabelText(/arten/i));
    const listbox = screen.getByRole('listbox');
    const options = within(listbox).getAllByRole('option');
    expect(options.map((o) => o.textContent)).toEqual(['Ocimum basilicum']);
  });

  it('removes the last chip on Backspace from an empty input', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm defaultValue={['sp-monstera', 'sp-basil']} />);
    const input = screen.getByLabelText(/arten/i);
    await user.click(input);
    await user.keyboard('{Escape}{Backspace}');
    expect(screen.queryByText('Ocimum basilicum')).not.toBeInTheDocument();
    expect(screen.getByText('Fensterblatt (Monstera deliciosa)')).toBeInTheDocument();
  });

  it('is disabled when the disabled prop is set', () => {
    renderWithProviders(<TestForm disabled />);
    expect(screen.getByLabelText(/arten/i)).toBeDisabled();
  });
});
