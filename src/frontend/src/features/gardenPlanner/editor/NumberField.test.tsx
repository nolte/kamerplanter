/**
 * #2905 (UI-NFR-007 R-014): the position/size field of the properties panel writes the stored value with the
 * decimal separator of the UI language ("0,9" in German, "0.9" in English) and reads both separators back. A value
 * shown by the field and committed unchanged does not drift: blur without an edit commits nothing.
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/i18n/i18n';
import { NumberField } from './NumberField';

const original = i18n.language;
beforeEach(() => cleanup());
afterEach(async () => {
  cleanup();
  await act(() => i18n.changeLanguage(original));
});

const field = (): HTMLInputElement => screen.getByTestId('number-field') as HTMLInputElement;

function renderField(value: number, onCommit = vi.fn()) {
  const view = render(<NumberField label="Width" value={value} unit="m" testId="number-field" onCommit={onCommit} />);
  return { ...view, onCommit };
}

describe('NumberField locale display (#2905)', () => {
  it.each([
    ['de', '0,9'],
    ['en', '0.9'],
  ])('shows 0.9 with the separator of %s', async (language, shown) => {
    await act(() => i18n.changeLanguage(language));
    renderField(0.9);
    expect(field()).toHaveValue(shown);
  });

  it.each(['de', 'en'])('keeps every digit and adds no grouping (%s)', async (language) => {
    await act(() => i18n.changeLanguage(language));
    renderField(1234.567);
    expect(field()).toHaveValue(language === 'de' ? '1234,567' : '1234.567');
  });

  it('follows the stored value and a language switch', async () => {
    await act(() => i18n.changeLanguage('de'));
    const { rerender } = renderField(1.8);
    expect(field()).toHaveValue('1,8');
    rerender(<NumberField label="Width" value={5.5} unit="m" testId="number-field" onCommit={vi.fn()} />);
    expect(field()).toHaveValue('5,5');
    await act(() => i18n.changeLanguage('en'));
    expect(field()).toHaveValue('5.5');
  });

  it('puts the stored value back in the UI language on Escape', async () => {
    await act(() => i18n.changeLanguage('de'));
    renderField(0.9);
    fireEvent.change(field(), { target: { value: '2' } });
    fireEvent.keyDown(field(), { key: 'Escape' });
    expect(field()).toHaveValue('0,9');
  });
});

describe('NumberField round trip (#2905)', () => {
  it.each(['de', 'en'])('commits nothing when the shown value is blurred unchanged (%s)', async (language) => {
    await act(() => i18n.changeLanguage(language));
    const { onCommit } = renderField(0.3);
    fireEvent.blur(field());
    expect(onCommit).not.toHaveBeenCalled();
  });

  it.each([
    ['de', '2,25'],
    ['de', '2.25'],
    ['en', '2.25'],
    ['en', '2,25'],
  ])('reads %s input "%s" as the number 2.25', async (language, typed) => {
    await act(() => i18n.changeLanguage(language));
    const { onCommit } = renderField(1);
    fireEvent.change(field(), { target: { value: typed } });
    fireEvent.blur(field());
    expect(onCommit).toHaveBeenCalledExactlyOnceWith(2.25, 1);
  });
});
