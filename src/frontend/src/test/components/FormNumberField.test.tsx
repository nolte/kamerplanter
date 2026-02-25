import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';

const schema = z.object({ count: z.number().min(1).max(10) });

function TestForm() {
  const { control, handleSubmit } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { count: 1 },
  });
  return (
    <form onSubmit={handleSubmit(() => {})}>
      <FormNumberField name="count" control={control} label="Count" min={1} max={10} />
      <button type="submit">Submit</button>
    </form>
  );
}

describe('FormNumberField', () => {
  it('renders with label', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/count/i)).toBeTruthy();
  });

  it('has number type', () => {
    render(<TestForm />);
    const input = screen.getByLabelText(/count/i);
    expect(input).toHaveAttribute('type', 'number');
  });

  it('accepts number input', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    const input = screen.getByLabelText(/count/i);
    await user.clear(input);
    await user.type(input, '5');
    expect(input).toHaveValue(5);
  });

  it('renders default value', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/count/i)).toHaveValue(1);
  });
});
