import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import Form from '@/components/form/Form';
import FormSelectField from '@/components/form/FormSelectField';

const options = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

function TestForm() {
  const { control } = useForm({ defaultValues: { level: 'low' } });
  return (
    <Form>
      <FormSelectField name="level" control={control} label="Level" options={options} />
    </Form>
  );
}

describe('FormSelectField', () => {
  it('renders label', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/level/i)).toBeTruthy();
  });

  it('has default value', () => {
    render(<TestForm />);
    expect(screen.getByText('Low')).toBeTruthy();
  });

  it('opens options on click', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    await user.click(screen.getByLabelText(/level/i));
    expect(screen.getByRole('listbox')).toBeTruthy();
    expect(screen.getAllByRole('option').length).toBe(3);
  });
});
