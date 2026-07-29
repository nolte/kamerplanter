import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import Form from '@/components/form/Form';
import FormTimezoneField from '@/components/form/FormTimezoneField';

function TestForm({ initial = 'UTC' }: { initial?: string }) {
  const { control } = useForm({ defaultValues: { timezone: initial } });
  return (
    <Form>
      <FormTimezoneField name="timezone" control={control} label="Timezone" />
    </Form>
  );
}

function input() {
  return within(screen.getByTestId('form-field-timezone')).getByRole('combobox') as HTMLInputElement;
}

describe('FormTimezoneField', () => {
  it('renders the current value in a searchable combobox', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/timezone/i)).toBeTruthy();
    expect(input().value).toBe('UTC');
  });

  it('filters zones as the user types and selects one', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    const field = input();
    await user.clear(field);
    await user.type(field, 'Europe/Ber');
    await user.click(await screen.findByRole('option', { name: 'Europe/Berlin' }));
    expect(input().value).toBe('Europe/Berlin');
  });

  it('keeps an initial value that is not in the base list selectable', () => {
    // A value the runtime may not enumerate must still show up.
    render(<TestForm initial="Factory" />);
    expect(input().value).toBe('Factory');
  });
});
