import { screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import WaterSourceSection, { TAP_WATER_DEFAULTS } from '@/components/water/WaterSourceSection';
import type { SiteWaterConfig, WaterSourceWarning } from '@/api/types';
import { renderWithProviders, createTestStore } from '../helpers';
import { toggleShowAllFields } from '@/store/slices/uiSlice';

/** Build a store with the "show all fields" override on, exposing the expert fields. */
function expertStore() {
  const store = createTestStore();
  store.dispatch(toggleShowAllFields());
  return store;
}

const defaultConfig: SiteWaterConfig = {
  has_ro_system: false,
  tap_water_profile: null,
  ro_water_profile: null,
};

describe('WaterSourceSection', () => {
  it('renders water config heading', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/Wasserquelle|Water Source/i)).toBeTruthy();
  });

  it('renders tap water EC and pH fields', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.getByTestId('tap-ec')).toBeTruthy();
    expect(screen.getByTestId('tap-ph')).toBeTruthy();
  });

  it('does not show RO fields when has_ro_system is false', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.queryByTestId('ro-ec')).toBeNull();
    expect(screen.queryByTestId('ro-ph')).toBeNull();
  });

  it('shows RO fields when has_ro_system is true', () => {
    const config: SiteWaterConfig = {
      ...defaultConfig,
      has_ro_system: true,
    };
    renderWithProviders(
      <WaterSourceSection value={config} onChange={vi.fn()} />,
    );
    expect(screen.getByTestId('ro-ec')).toBeTruthy();
    expect(screen.getByTestId('ro-ph')).toBeTruthy();
  });

  it('calls onChange when RO toggle is clicked', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={onChange} />,
    );
    const toggle = screen.getByTestId('ro-system-toggle');
    fireEvent.click(toggle);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ has_ro_system: true }),
    );
  });

  it('displays warnings', () => {
    const warnings: WaterSourceWarning[] = [
      { code: 'gh_plausibility', message: 'GH mismatch', severity: 'warning' },
      { code: 'ro_membrane', message: 'RO EC high', severity: 'warning' },
    ];
    renderWithProviders(
      <WaterSourceSection
        value={defaultConfig}
        onChange={vi.fn()}
        warnings={warnings}
      />,
    );
    expect(screen.getByTestId('water-warning-gh_plausibility')).toBeTruthy();
    expect(screen.getByTestId('water-warning-ro_membrane')).toBeTruthy();
  });

  it('renders an info severity for non-warning codes', () => {
    const warnings: WaterSourceWarning[] = [
      { code: 'measurement_age', message: 'Messung alt', severity: 'info' },
    ];
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} warnings={warnings} />,
    );
    expect(screen.getByTestId('water-warning-measurement_age')).toBeTruthy();
  });

  it('propagates a changed tap water EC value', () => {
    const onChange = vi.fn();
    renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />);
    const ecInput = within(screen.getByTestId('tap-ec')).getByRole('spinbutton');
    fireEvent.change(ecInput, { target: { value: '0.45' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        tap_water_profile: expect.objectContaining({ ec_ms: 0.45 }),
      }),
    );
  });

  it('coerces an empty tap pH input to zero', () => {
    const onChange = vi.fn();
    renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />);
    const phInput = within(screen.getByTestId('tap-ph')).getByRole('spinbutton');
    fireEvent.change(phInput, { target: { value: '' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        tap_water_profile: expect.objectContaining({ ph: 0 }),
      }),
    );
  });

  it('seeds tap defaults from an existing profile on change', () => {
    const onChange = vi.fn();
    const config: SiteWaterConfig = {
      ...defaultConfig,
      tap_water_profile: { ...TAP_WATER_DEFAULTS, ec_ms: 0.5 },
    };
    renderWithProviders(<WaterSourceSection value={config} onChange={onChange} />);
    const ecInput = within(screen.getByTestId('tap-ec')).getByRole('spinbutton');
    expect((ecInput as HTMLInputElement).value).toBe('0.5');
  });

  it('propagates a changed RO water EC value', () => {
    const onChange = vi.fn();
    const config: SiteWaterConfig = { ...defaultConfig, has_ro_system: true };
    renderWithProviders(<WaterSourceSection value={config} onChange={onChange} />);
    const roEc = within(screen.getByTestId('ro-ec')).getByRole('spinbutton');
    fireEvent.change(roEc, { target: { value: '0.03' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        ro_water_profile: expect.objectContaining({ ec_ms: 0.03 }),
      }),
    );
  });

  it('propagates a changed RO water pH value', () => {
    const onChange = vi.fn();
    const config: SiteWaterConfig = { ...defaultConfig, has_ro_system: true };
    renderWithProviders(<WaterSourceSection value={config} onChange={onChange} />);
    const roPh = within(screen.getByTestId('ro-ph')).getByRole('spinbutton');
    fireEvent.change(roPh, { target: { value: '6.4' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        ro_water_profile: expect.objectContaining({ ph: 6.4 }),
      }),
    );
  });

  describe('with expert fields visible', () => {
    it('renders the expert tap-water fields', () => {
      renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={vi.fn()} />, {
        store: expertStore(),
      });
      // Alkalinity / GH etc. only render under the expertise wrapper.
      expect(screen.getByLabelText(/alkalinity|alkalinität/i)).toBeTruthy();
    });

    it('propagates a changed alkalinity value', () => {
      const onChange = vi.fn();
      renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />, {
        store: expertStore(),
      });
      const input = screen.getByLabelText(/alkalinity|alkalinität/i);
      fireEvent.change(input, { target: { value: '120' } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ alkalinity_ppm: 120 }),
        }),
      );
    });

    it('propagates a changed measurement date', () => {
      const onChange = vi.fn();
      renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />, {
        store: expertStore(),
      });
      const dateInput = screen.getByLabelText(/measurement date|messdatum/i);
      fireEvent.change(dateInput, { target: { value: '2026-04-01' } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ measurement_date: '2026-04-01' }),
        }),
      );
    });

    it.each([
      [/general hardness|gesamthärte/i, 'gh_ppm', '150'],
      [/^calcium/i, 'calcium_ppm', '40'],
      [/^magnesium/i, 'magnesium_ppm', '12'],
      [/^chlorine|chlor \(/i, 'chlorine_ppm', '0.3'],
      [/chloramine|chloramin/i, 'chloramine_ppm', '0.1'],
    ])('propagates a changed %s value', (labelRe, field, value) => {
      const onChange = vi.fn();
      renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />, {
        store: expertStore(),
      });
      const input = screen.getByLabelText(labelRe);
      fireEvent.change(input, { target: { value } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ [field]: Number(value) }),
        }),
      );
    });

    it('propagates a changed source note', () => {
      const onChange = vi.fn();
      renderWithProviders(<WaterSourceSection value={defaultConfig} onChange={onChange} />, {
        store: expertStore(),
      });
      const input = screen.getByLabelText(/source|quelle/i);
      fireEvent.change(input, { target: { value: 'Municipal' } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ source_note: 'Municipal' }),
        }),
      );
    });

    it('clears the source note to null when emptied', () => {
      const onChange = vi.fn();
      const config: SiteWaterConfig = {
        ...defaultConfig,
        tap_water_profile: { ...TAP_WATER_DEFAULTS, source_note: 'Well' },
      };
      renderWithProviders(<WaterSourceSection value={config} onChange={onChange} />, {
        store: expertStore(),
      });
      const input = screen.getByLabelText(/source|quelle/i);
      fireEvent.change(input, { target: { value: '' } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ source_note: null }),
        }),
      );
    });

    it('clears the measurement date to null when emptied', () => {
      const onChange = vi.fn();
      const config: SiteWaterConfig = {
        ...defaultConfig,
        tap_water_profile: { ...TAP_WATER_DEFAULTS, measurement_date: '2026-04-01' },
      };
      renderWithProviders(<WaterSourceSection value={config} onChange={onChange} />, {
        store: expertStore(),
      });
      const dateInput = screen.getByLabelText(/measurement date|messdatum/i);
      fireEvent.change(dateInput, { target: { value: '' } });
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tap_water_profile: expect.objectContaining({ measurement_date: null }),
        }),
      );
    });
  });
});
