/**
 * #2905 (UI-NFR-007 R-014): an object property (sill height, lamp height, ...) is shown with the decimal separator of
 * the UI language ("0,9" in German, "0.9" in English); both separators are read back as the same number, and a value
 * blurred unchanged commits nothing (no drift through the field).
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/i18n/i18n';
import { PropNumberField } from './PropNumberField';

const original = i18n.language;
beforeEach(() => cleanup());
afterEach(async () => {
  cleanup();
  await act(() => i18n.changeLanguage(original));
});

const field = (): HTMLInputElement => screen.getByTestId('prop-field') as HTMLInputElement;

function element(value: number | null, onCommit: (value: number | null) => void) {
  return (
    <PropNumberField
      label="Sill height"
      value={value}
      unit="m"
      min={0}
      max={10}
      helperText="help"
      invalidText="invalid"
      testId="prop-field"
      onCommit={onCommit}
    />
  );
}

function renderField(value: number | null) {
  const onCommit = vi.fn();
  const view = render(element(value, onCommit));
  return { ...view, onCommit };
}

describe('PropNumberField locale display (#2905)', () => {
  it.each([
    ['de', '0,9'],
    ['en', '0.9'],
  ])('shows 0.9 with the separator of %s', async (language, shown) => {
    await act(() => i18n.changeLanguage(language));
    renderField(0.9);
    expect(field()).toHaveValue(shown);
  });

  it.each(['de', 'en'])('shows an empty optional value as an empty field (%s)', async (language) => {
    await act(() => i18n.changeLanguage(language));
    renderField(null);
    expect(field()).toHaveValue('');
  });

  it('follows an undo and a language switch', async () => {
    await act(() => i18n.changeLanguage('de'));
    const { rerender } = renderField(1.8);
    expect(field()).toHaveValue('1,8');
    rerender(element(3.6, vi.fn()));
    expect(field()).toHaveValue('3,6');
    await act(() => i18n.changeLanguage('en'));
    expect(field()).toHaveValue('3.6');
  });

  it('puts the stored value back in the UI language on Escape', async () => {
    await act(() => i18n.changeLanguage('de'));
    renderField(0.9);
    fireEvent.change(field(), { target: { value: '4' } });
    fireEvent.keyDown(field(), { key: 'Escape' });
    expect(field()).toHaveValue('0,9');
  });
});

describe('PropNumberField round trip (#2905)', () => {
  it.each(['de', 'en'])('commits nothing when the shown value is blurred unchanged (%s)', async (language) => {
    await act(() => i18n.changeLanguage(language));
    const { onCommit } = renderField(0.9);
    fireEvent.blur(field());
    expect(onCommit).not.toHaveBeenCalled();
  });

  it.each([
    ['de', '1,25'],
    ['de', '1.25'],
    ['en', '1.25'],
    ['en', '1,25'],
  ])('reads %s input "%s" as the number 1.25', async (language, typed) => {
    await act(() => i18n.changeLanguage(language));
    const { onCommit } = renderField(0.9);
    fireEvent.change(field(), { target: { value: typed } });
    fireEvent.blur(field());
    expect(onCommit).toHaveBeenCalledExactlyOnceWith(1.25);
  });
});
