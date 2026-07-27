import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormMonthField from '@/components/form/FormMonthField';

// Mirrors the overwintering schema: a required month is an integer 1–12, while
// the optional month additionally accepts '' (cleared via the empty option).
const schema = z.object({
  month: z.number().int().min(1).max(12),
  optionalMonth: z.union([z.number().int().min(1).max(12), z.literal('')]),
});
type FormData = z.infer<typeof schema>;

function TestForm({ onSubmit }: { onSubmit: (data: FormData) => void }) {
  const { control, handleSubmit } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { month: 10, optionalMonth: '' },
  });
  return (
    <Form onSubmit={handleSubmit(onSubmit)}>
      <FormMonthField name="month" control={control} label="Action month" required />
      <FormMonthField
        name="optionalMonth"
        control={control}
        label="Spring month"
        includeEmpty
      />
      <button type="submit">Submit</button>
    </Form>
  );
}

async function openField(testId: string) {
  const user = userEvent.setup();
  const field = screen.getByTestId(testId);
  await user.click(within(field).getByRole('combobox'));
  return screen.findByRole('listbox');
}

async function selectByLabel(testId: string, optionLabel: string) {
  const user = userEvent.setup();
  const listbox = await openField(testId);
  await user.click(within(listbox).getByText(optionLabel));
  await waitFor(() => expect(screen.queryByRole('listbox')).toBeNull());
}

describe('FormMonthField', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the twelve localised month names in the dropdown', async () => {
    render(<TestForm onSubmit={vi.fn()} />);

    const listbox = await openField('form-field-month');
    expect(within(listbox).getAllByRole('option')).toHaveLength(12);
    // Localised (de) month names, not raw numbers.
    expect(within(listbox).getByText('Januar')).toBeTruthy();
    expect(within(listbox).getByText('Oktober')).toBeTruthy();
    expect(within(listbox).getByText('Dezember')).toBeTruthy();
  });

  it('shows the default numeric value as its localised month name', () => {
    render(<TestForm onSubmit={vi.fn()} />);
    // Default month = 10 → "Oktober" is displayed in the combobox.
    const field = screen.getByTestId('form-field-month');
    expect(within(field).getByText('Oktober')).toBeTruthy();
  });

  it('submits the selected month as an integer 1–12', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<TestForm onSubmit={onSubmit} />);

    await selectByLabel('form-field-month', 'März');
    await user.click(screen.getByRole('button', { name: 'Submit' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    const submitted = onSubmit.mock.calls[0][0] as FormData;
    expect(submitted.month).toBe(3);
    expect(typeof submitted.month).toBe('number');
  });

  it('offers an empty option and stays optional when left empty', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<TestForm onSubmit={onSubmit} />);

    // The optional field exposes a leading empty option ("Keine").
    const listbox = await openField('form-field-optionalMonth');
    expect(within(listbox).getByText('Keine')).toBeTruthy();
    expect(within(listbox).getAllByRole('option')).toHaveLength(13);
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('listbox')).toBeNull());

    // Submitting without choosing a spring month is valid and yields ''.
    await user.click(screen.getByRole('button', { name: 'Submit' }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect((onSubmit.mock.calls[0][0] as FormData).optionalMonth).toBe('');
  });

  it('clears the optional field back to empty via the empty option', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<TestForm onSubmit={onSubmit} />);

    // Pick a month, then reset to the empty option.
    await selectByLabel('form-field-optionalMonth', 'Mai');
    await selectByLabel('form-field-optionalMonth', 'Keine');

    await user.click(screen.getByRole('button', { name: 'Submit' }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect((onSubmit.mock.calls[0][0] as FormData).optionalMonth).toBe('');
  });
});
