import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { useForm } from 'react-hook-form';
import FormDateField from '@/components/form/FormDateField';
import FormTimeField from '@/components/form/FormTimeField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormMultiSelectField from '@/components/form/FormMultiSelectField';
import FormRow from '@/components/form/FormRow';

describe('FormDateField', () => {
  function DateForm() {
    const { control } = useForm({ defaultValues: { sown_on: '2026-01-15' } });
    return <FormDateField name="sown_on" control={control} label="Aussaat" required />;
  }

  it('renders a date input with the default value', () => {
    render(<DateForm />);
    const input = screen.getByLabelText(/aussaat/i) as HTMLInputElement;
    expect(input.type).toBe('date');
    expect(input.value).toBe('2026-01-15');
  });

  it('updates the value on user input', async () => {
    const user = userEvent.setup();
    render(<DateForm />);
    const input = screen.getByLabelText(/aussaat/i) as HTMLInputElement;
    await user.clear(input);
    await user.type(input, '2026-03-20');
    expect(input.value).toBe('2026-03-20');
  });
});

describe('FormTimeField', () => {
  function TimeForm({ defaultValue }: { defaultValue?: string }) {
    const { control } = useForm({ defaultValues: { reminder: defaultValue ?? '' } });
    return <FormTimeField name="reminder" control={control} label="Uhrzeit" helperText="HH:MM" />;
  }

  it('renders a time input', () => {
    render(<TimeForm defaultValue="08:30" />);
    const input = screen.getByLabelText(/uhrzeit/i) as HTMLInputElement;
    expect(input.type).toBe('time');
    expect(input.value).toBe('08:30');
  });

  it('coerces a null value to an empty string', () => {
    render(<TimeForm />);
    const input = screen.getByLabelText(/uhrzeit/i) as HTMLInputElement;
    expect(input.value).toBe('');
  });

  it('shows the helper text', () => {
    render(<TimeForm />);
    expect(screen.getByText('HH:MM')).toBeTruthy();
  });
});

describe('FormSwitchField', () => {
  function SwitchForm({ defaultValue = false }: { defaultValue?: boolean }) {
    const { control } = useForm({ defaultValues: { active: defaultValue } });
    return <FormSwitchField name="active" control={control} label="Aktiv" helperText="Hinweis" />;
  }

  it('reflects the default checked state', () => {
    render(<SwitchForm defaultValue />);
    expect((screen.getByRole('switch') as HTMLInputElement).checked).toBe(true);
  });

  it('toggles when clicked', async () => {
    const user = userEvent.setup();
    render(<SwitchForm />);
    const toggle = screen.getByRole('switch') as HTMLInputElement;
    expect(toggle.checked).toBe(false);
    await user.click(toggle);
    expect(toggle.checked).toBe(true);
  });

  it('renders the helper text', () => {
    render(<SwitchForm />);
    expect(screen.getByText('Hinweis')).toBeTruthy();
  });
});

describe('FormMultiSelectField', () => {
  const options = [
    { value: 'spring', label: 'Frühling' },
    { value: 'summer', label: 'Sommer' },
    { value: 'autumn', label: 'Herbst' },
  ];

  function MultiForm({ defaultValue = [] as string[] }: { defaultValue?: string[] }) {
    const { control } = useForm({ defaultValues: { seasons: defaultValue } });
    return (
      <FormMultiSelectField
        name="seasons"
        control={control}
        label="Saisons"
        options={options}
        helperText="Mehrfachauswahl"
      />
    );
  }

  it('renders selected values as chips', () => {
    render(<MultiForm defaultValue={['spring', 'summer']} />);
    expect(screen.getByText('Frühling')).toBeTruthy();
    expect(screen.getByText('Sommer')).toBeTruthy();
  });

  it('opens the multi-select listbox with all options', async () => {
    const user = userEvent.setup();
    render(<MultiForm />);
    await user.click(screen.getByLabelText(/saisons/i));
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getAllByRole('option').length).toBe(3);
  });

  it('adds an option to the selection', async () => {
    const user = userEvent.setup();
    render(<MultiForm />);
    await user.click(screen.getByLabelText(/saisons/i));
    const option = screen.getByRole('option', { name: 'Herbst' });
    await user.click(option);
    expect(option.getAttribute('aria-selected')).toBe('true');
  });
});

describe('FormRow', () => {
  it('renders its children', () => {
    render(
      <FormRow>
        <span>links</span>
        <span>rechts</span>
      </FormRow>,
    );
    expect(screen.getByText('links')).toBeTruthy();
    expect(screen.getByText('rechts')).toBeTruthy();
  });
});
