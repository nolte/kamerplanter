import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { useForm, useWatch, type Control } from 'react-hook-form';
import PlantInstanceAutocompleteField from '@/components/form/PlantInstanceAutocompleteField';
import PlantInstancePicker from '@/components/form/PlantInstancePicker';
import type { PlantInstance } from '@/api/types';
import { renderWithProviders } from '../helpers';

const instances: PlantInstance[] = [
  {
    key: 'inst-tomato',
    instance_id: 'TOM-001',
    plant_name: 'Big Red',
    species: { scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'] },
  } as unknown as PlantInstance,
  {
    key: 'inst-basil',
    instance_id: 'BAS-002',
    plant_name: null,
    species: { scientific_name: 'Ocimum basilicum', common_names: ['Basil'] },
  } as unknown as PlantInstance,
];

// ---- RHF field variant ------------------------------------------------------

function SingleForm({ defaultValue = '' }: { defaultValue?: string }) {
  const { control } = useForm({ defaultValues: { plant_key: defaultValue } });
  return (
    <PlantInstanceAutocompleteField
      name="plant_key"
      control={control}
      label="Pflanze"
      instances={instances}
    />
  );
}

function SelectedKeys({ control }: { control: Control<{ plant_keys: string[] }> }) {
  const value = useWatch({ control, name: 'plant_keys' });
  return <output data-testid="selected-keys">{value.join(',')}</output>;
}

function MultiForm() {
  const { control } = useForm<{ plant_keys: string[] }>({
    defaultValues: { plant_keys: [] },
  });
  return (
    <>
      <PlantInstanceAutocompleteField
        name="plant_keys"
        control={control}
        label="Pflanzen"
        instances={instances}
        multiple
      />
      <SelectedKeys control={control} />
    </>
  );
}

describe('PlantInstanceAutocompleteField', () => {
  it('renders a labelled autocomplete input', () => {
    renderWithProviders(<SingleForm />);
    expect(screen.getByLabelText(/pflanze/i)).toBeTruthy();
  });

  it('shows the human-readable name for a preselected key (never the key)', () => {
    renderWithProviders(<SingleForm defaultValue="inst-tomato" />);
    const input = screen.getByLabelText(/pflanze/i) as HTMLInputElement;
    expect(input.value).toBe('Big Red');
    expect(input.value).not.toContain('inst-tomato');
  });

  it('falls back to instance_id when there is no plant_name', () => {
    renderWithProviders(<SingleForm defaultValue="inst-basil" />);
    const input = screen.getByLabelText(/pflanze/i) as HTMLInputElement;
    expect(input.value).toBe('BAS-002');
  });

  it('filters options by typing a species name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SingleForm />);
    const input = screen.getByLabelText(/pflanze/i);
    await user.click(input);
    await user.type(input, 'Solanum');
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getAllByRole('option').length).toBe(1);
  });

  it('multi-select collects several keys', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiForm />);
    const input = screen.getByLabelText(/pflanzen/i);
    await user.click(input);
    await user.click(await screen.findByRole('option', { name: /Big Red/ }));
    await user.click(input);
    await user.click(await screen.findByRole('option', { name: /BAS-002/ }));
    expect(screen.getByTestId('selected-keys')).toHaveTextContent('inst-tomato,inst-basil');
  });
});

// ---- Controlled (non-RHF) variant ------------------------------------------

describe('PlantInstancePicker (controlled)', () => {
  it('emits the internal key on selection, not the displayed name', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithProviders(
      <PlantInstancePicker
        label="Pflanze"
        instances={instances}
        value=""
        onChange={onChange}
        testId="picker"
      />,
    );
    const input = screen.getByLabelText(/pflanze/i);
    await user.click(input);
    await user.click(await screen.findByRole('option', { name: /Big Red/ }));
    expect(onChange).toHaveBeenCalledWith('inst-tomato');
  });

  it('renders the name for a controlled key value', () => {
    renderWithProviders(
      <PlantInstancePicker
        label="Pflanze"
        instances={instances}
        value="inst-tomato"
        onChange={vi.fn()}
      />,
    );
    const input = screen.getByLabelText(/pflanze/i) as HTMLInputElement;
    expect(input.value).toBe('Big Red');
  });

  it('clears the selection back to an empty key', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithProviders(
      <PlantInstancePicker
        label="Pflanze"
        instances={instances}
        value="inst-tomato"
        onChange={onChange}
      />,
    );
    await user.click(screen.getByLabelText(/clear/i));
    expect(onChange).toHaveBeenCalledWith('');
  });
});
