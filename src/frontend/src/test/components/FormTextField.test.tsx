import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';

const schema = z.object({ name: z.string().min(1, 'Name is required') });

function TestForm({ defaultName = '' }: { defaultName?: string }) {
  const { control, handleSubmit } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: defaultName },
  });
  return (
    <form onSubmit={handleSubmit(() => {})}>
      <FormTextField name="name" control={control} label="Name" required />
      <button type="submit">Submit</button>
    </form>
  );
}

describe('FormTextField', () => {
  it('renders label', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/name/i)).toBeTruthy();
  });

  it('accepts user input', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    const input = screen.getByLabelText(/name/i);
    await user.type(input, 'Test');
    expect(input).toHaveValue('Test');
  });

  it('is fullWidth', () => {
    const { container } = render(<TestForm />);
    const formControl = container.querySelector('.MuiFormControl-fullWidth');
    expect(formControl).toBeTruthy();
  });

  it('renders with default value', () => {
    render(<TestForm defaultName="Hello" />);
    expect(screen.getByLabelText(/name/i)).toHaveValue('Hello');
  });
});
