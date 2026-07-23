import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import FormClimateZoneField from '@/components/form/FormClimateZoneField';
import { USDA_HARDINESS_ZONES } from '@/pages/standorte/climateZones';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';

function TestForm({ initial = '' }: { initial?: string }) {
  const { control } = useForm({ defaultValues: { climate_zone: initial } });
  return (
    <form>
      <FormClimateZoneField name="climate_zone" control={control} label="Climate" />
    </form>
  );
}

// The field embeds a `HelpTooltip` (UI-NFR-011 — "hardiness_zones" glossary
// term), which reads the active experience level from Redux. Render through
// `renderWithProviders` (like every other HelpTooltip-consuming test in this
// suite) instead of the bare `@testing-library/react` `render`.
function renderField(props: { initial?: string } = {}) {
  return renderWithProviders(<TestForm {...props} />, { store: createStoreWithExpertise('expert') });
}

describe('FormClimateZoneField', () => {
  it('renders the label', () => {
    renderField();
    expect(screen.getByLabelText(/climate/i)).toBeTruthy();
  });

  it('offers the empty option plus every USDA half-zone', async () => {
    const user = userEvent.setup();
    renderField();
    await user.click(screen.getByLabelText(/climate/i));
    // "not specified" + 26 zones (1a..13b).
    expect(screen.getAllByRole('option').length).toBe(USDA_HARDINESS_ZONES.length + 1);
    expect(screen.getByTestId('form-option-climate_zone-8b')).toBeTruthy();
    expect(screen.getByTestId('form-option-climate_zone-none')).toBeTruthy();
  });

  it('selects a zone and reflects it in the field', async () => {
    const user = userEvent.setup();
    renderField();
    await user.click(screen.getByLabelText(/climate/i));
    await user.click(screen.getByTestId('form-option-climate_zone-7a'));
    expect(within(screen.getByTestId('form-field-climate_zone')).getByText('7a')).toBeTruthy();
  });

  it('keeps a legacy free-text value selectable', async () => {
    const user = userEvent.setup();
    renderField({ initial: 'temperate' });
    // The stored value shows without being one of the USDA zones.
    expect(within(screen.getByTestId('form-field-climate_zone')).getByText('temperate')).toBeTruthy();
    await user.click(screen.getByLabelText(/climate/i));
    expect(screen.getByTestId('form-option-climate_zone-temperate')).toBeTruthy();
    // Extra legacy option is appended on top of the empty + USDA options.
    expect(screen.getAllByRole('option').length).toBe(USDA_HARDINESS_ZONES.length + 2);
  });
});
