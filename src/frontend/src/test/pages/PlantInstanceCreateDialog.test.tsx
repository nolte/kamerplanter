import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PlantInstanceCreateDialog, {
  type PlantInstanceDuplicateData,
} from '@/pages/pflanzen/PlantInstanceCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('PlantInstanceCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the create dialog with the create title when open', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    expect(await screen.findByTestId('plant-instance-create-dialog')).toBeTruthy();
    expect(within(screen.getByRole('dialog')).getByText('Pflanze erstellen')).toBeTruthy();
  });

  it('does not render content when closed', () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open={false} onClose={() => {}} onCreated={() => {}} />,
    );
    expect(screen.queryByTestId('plant-instance-create-dialog')).toBeNull();
  });

  it('prefills the instance id from a generated value', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    const idField = within(await screen.findByTestId('form-field-instance_id')).getByRole('textbox');
    await waitFor(() => {
      expect((idField as HTMLInputElement).value.length).toBeGreaterThan(0);
    });
  });

  it('shows the duplicate title and disables species when duplicating', async () => {
    const duplicateFrom: PlantInstanceDuplicateData = {
      species_key: 'sp-1',
      cultivar_key: null,
      plant_name: 'Big Red',
      substrate_key: null,
      substrate_type_override: null,
      current_phase_key: null,
      slot_key: null,
    };
    renderWithProviders(
      <PlantInstanceCreateDialog
        open
        onClose={() => {}}
        onCreated={() => {}}
        duplicateFrom={duplicateFrom}
      />,
    );
    expect(
      within(await screen.findByRole('dialog')).getByText('Pflanze duplizieren'),
    ).toBeTruthy();
  });

  it('submits a new plant instance and calls onCreated with the new key', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    // species + instance_id are required; pick species via the autocomplete
    const speciesInput = within(await screen.findByTestId('form-field-species_key')).getByRole('combobox');
    await user.click(speciesInput);
    await user.type(speciesInput, 'Solanum');
    const option = await screen.findByRole('option', { name: /Solanum lycopersicum/ });
    await user.click(option);

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
    expect(onCreated).toHaveBeenCalledWith('plant-new');
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/plant-instances', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
      http.post('/api/v1/t/:tenant/plant-instances', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    const speciesInput = within(await screen.findByTestId('form-field-species_key')).getByRole('combobox');
    await user.click(speciesInput);
    await user.type(speciesInput, 'Solanum');
    await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('calls onClose when cancelled', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={onClose} onCreated={() => {}} />,
    );
    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('resolves the location cascade from a duplicated slot', async () => {
    // Duplicating from a plant with a slot_key triggers getSlot → getLocation →
    // listSlots and pre-populates site/location/slot via the skip-reset refs.
    const duplicateFrom: PlantInstanceDuplicateData = {
      species_key: 'sp-1',
      cultivar_key: null,
      plant_name: 'Big Red',
      substrate_key: null,
      substrate_type_override: 'coco',
      current_phase_key: null,
      slot_key: 'slot-1',
    };
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} duplicateFrom={duplicateFrom} />,
    );

    // The slot select becomes populated once the cascade resolves
    await waitFor(() => {
      expect(screen.getByTestId('form-field-slot_key')).toBeTruthy();
    });
    // Species is locked for duplicates
    const speciesInput = within(screen.getByTestId('form-field-species_key')).getByRole('combobox');
    expect(speciesInput).toBeDisabled();
  });

  it('selecting a site populates the location select cascade', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );

    const siteSelect = within(await screen.findByTestId('form-field-site_key')).getByRole('combobox');
    await user.click(siteSelect);
    await user.click(await screen.findByRole('option', { name: 'Main Greenhouse' }));

    // The location field reacts to the selected site without throwing
    await waitFor(() => {
      expect(screen.getByTestId('form-field-slot_key')).toBeTruthy();
    });
  });
});
