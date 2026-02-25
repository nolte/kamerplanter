import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import FormChipInput from '@/components/form/FormChipInput';

function TestForm() {
  const { control } = useForm({ defaultValues: { tags: ['existing'] } });
  return (
    <form>
      <FormChipInput name="tags" control={control} label="Tags" />
    </form>
  );
}

function EmptyForm() {
  const { control } = useForm({ defaultValues: { tags: [] as string[] } });
  return (
    <form>
      <FormChipInput name="tags" control={control} label="Tags" />
    </form>
  );
}

describe('FormChipInput', () => {
  it('renders label', () => {
    render(<TestForm />);
    expect(screen.getByLabelText(/tags/i)).toBeTruthy();
  });

  it('displays existing chips', () => {
    render(<TestForm />);
    expect(screen.getByText('existing')).toBeTruthy();
  });

  it('adds chip on Enter', async () => {
    const user = userEvent.setup();
    render(<EmptyForm />);
    const input = screen.getByLabelText(/tags/i);
    await user.type(input, 'new-tag{Enter}');
    expect(screen.getByText('new-tag')).toBeTruthy();
  });

  it('does not add duplicate chips', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    const input = screen.getByLabelText(/tags/i);
    await user.type(input, 'existing{Enter}');
    const chips = screen.getAllByText('existing');
    expect(chips.length).toBe(1);
  });

  it('removes chip on delete', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    const deleteButton = screen.getByTestId('CancelIcon');
    await user.click(deleteButton);
    expect(screen.queryByText('existing')).toBeNull();
  });
});
