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

  // #833 — pins the *decision*, not the rendered geometry.
  //
  // jsdom has no layout engine, so it cannot answer whether the list covers its
  // trigger; MUI resolves every origin against zero-sized rects here. What it can
  // hold in place is the capped height, which is the lever the real-viewport
  // measurement identified: at 393px the list cleared the field at 200/160/120px
  // and covered it at 240px, 320px and 45vh.
  //
  // The number is asserted deliberately rather than "some maxHeight is set":
  // raising it back to a roomier value *is* the regression, and it would read as an
  // improvement in review.
  it('caps the option list height so it can fit below its trigger (#833)', async () => {
    const user = userEvent.setup();
    render(<TestForm />);
    await user.click(screen.getByLabelText(/level/i));

    const paper = screen.getByRole('listbox').closest('.MuiPaper-root');
    expect(paper).not.toBeNull();
    expect(window.getComputedStyle(paper as HTMLElement).maxHeight).toBe('200px');
  });
});
