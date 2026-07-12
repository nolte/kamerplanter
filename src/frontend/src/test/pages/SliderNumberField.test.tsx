import { useState } from 'react';
import { fireEvent, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SliderNumberField from '@/pages/pflanzen/calculations/SliderNumberField';
import { renderWithProviders } from '../helpers';

interface HarnessProps {
  onChange: (v: number) => void;
  initial?: number;
  min?: number;
  max?: number;
}

/** Controlled wrapper so the field reflects clamped values back into the UI. */
function Harness({ onChange, initial = 20, min = 5, max = 40 }: HarnessProps) {
  const [value, setValue] = useState(initial);
  return (
    <SliderNumberField
      label="Temperature"
      value={value}
      onChange={(v) => {
        setValue(v);
        onChange(v);
      }}
      min={min}
      max={max}
      step={0.5}
      unit="°C"
      glossaryTerm="vpd"
      marks={[{ value: 5 }, { value: 40, label: '40' }]}
      helperText="helper text"
    />
  );
}

describe('SliderNumberField', () => {
  it('renders the numeric field, unit adornment and helper text', () => {
    renderWithProviders(<Harness onChange={vi.fn()} />);
    expect(screen.getByRole('spinbutton', { name: 'Temperature' })).toBeTruthy();
    expect(screen.getByText('°C')).toBeTruthy();
    expect(screen.getByText('helper text')).toBeTruthy();
    expect(screen.getByRole('slider', { name: 'Temperature' })).toBeTruthy();
  });

  it('clamps a below-minimum numeric entry up to min', () => {
    const onChange = vi.fn();
    renderWithProviders(<Harness onChange={onChange} min={5} max={40} />);

    const input = screen.getByRole('spinbutton', { name: 'Temperature' });
    fireEvent.change(input, { target: { value: '1' } });

    expect(onChange).toHaveBeenLastCalledWith(5);
  });

  it('clamps an above-maximum numeric entry down to max', () => {
    const onChange = vi.fn();
    renderWithProviders(<Harness onChange={onChange} min={5} max={40} />);

    const input = screen.getByRole('spinbutton', { name: 'Temperature' });
    fireEvent.change(input, { target: { value: '99' } });

    expect(onChange).toHaveBeenLastCalledWith(40);
  });

  it('emits the value when the slider is moved', () => {
    const onChange = vi.fn();
    renderWithProviders(<Harness onChange={onChange} />);

    const slider = screen.getByRole('slider', { name: 'Temperature' });
    fireEvent.change(slider, { target: { value: '30' } });

    expect(onChange).toHaveBeenCalledWith(30);
  });

  it('renders an error message and flags the field', () => {
    renderWithProviders(
      <SliderNumberField
        label="Humidity"
        value={50}
        onChange={vi.fn()}
        min={0}
        max={100}
        error="out of range"
        disabled
      />,
    );
    expect(screen.getByText('out of range')).toBeTruthy();
  });
});
