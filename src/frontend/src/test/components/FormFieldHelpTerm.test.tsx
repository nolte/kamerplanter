import { describe, it, expect } from 'vitest';
import { act, fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm } from 'react-hook-form';
import Form from '@/components/form/Form';
import FormNumberField from '@/components/form/FormNumberField';
import FormTextField from '@/components/form/FormTextField';
import FormSwitchField from '@/components/form/FormSwitchField';
import i18n from '@/i18n';
import { renderWithProviders } from '@/test/helpers';

/**
 * #3020 — the `helpTerm` slot of the `Form*Field` components (UI-NFR-011 §6.1).
 *
 * What the slot owes: the shared glossary trigger next to the field, a trigger with
 * a name of its own, and an untouched label↔input association — the help button
 * must neither sit inside the `<label>` (it would join the field's accessible name
 * and a click on it would toggle a switch) nor replace the field's focus stop.
 */

// Resolved through the running i18n instance, so the test holds in whichever
// language the suite runs in.
const short = (term: string) => i18n.t(`glossary.${term}.short`);

interface Values {
  ec: number | null;
  note: string;
  flushed: boolean;
  plain: number | null;
}

function TestForm({ withHelp = true }: { withHelp?: boolean }) {
  const { control } = useForm<Values>({
    defaultValues: { ec: null, note: '', flushed: false, plain: null },
  });
  return (
    <Form onSubmit={(e) => e.preventDefault()}>
      <FormNumberField name="ec" control={control} label="EC" helpTerm={withHelp ? 'ec' : undefined} />
      <FormTextField name="note" control={control} label="pH note" helpTerm={withHelp ? 'ph' : undefined} />
      <FormSwitchField
        name="flushed"
        control={control}
        label="Flushed"
        helpTerm={withHelp ? 'runoff' : undefined}
      />
      <FormNumberField name="plain" control={control} label="Plain" />
    </Form>
  );
}

function helpButton(term: string): HTMLElement {
  const button = screen.getByTestId(`help-tooltip-icon-${term}`).closest('button');
  if (!button) throw new Error(`no help button for ${term}`);
  return button;
}

describe('Form*Field helpTerm slot (#3020)', () => {
  it('renders a named help button for each field that sets helpTerm', () => {
    renderWithProviders(<TestForm />);
    expect(screen.getByRole('button', { name: short('ec') })).toBe(helpButton('ec'));
    expect(screen.getByRole('button', { name: short('ph') })).toBe(helpButton('ph'));
    expect(screen.getByRole('button', { name: short('runoff') })).toBe(helpButton('runoff'));
    // A field without helpTerm keeps its exact old shape: no trigger.
    expect(screen.queryAllByTestId(/^help-tooltip-icon-/)).toHaveLength(3);
  });

  it('renders no help trigger when helpTerm is absent', () => {
    renderWithProviders(<TestForm withHelp={false} />);
    expect(screen.queryByTestId(/^help-tooltip-icon-/)).toBeNull();
  });

  it('keeps the label association and keeps the trigger out of the field name', () => {
    renderWithProviders(<TestForm />);
    const ec = screen.getByLabelText('EC');
    expect(ec.tagName).toBe('INPUT');
    expect(ec).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('pH note').tagName).toBe('INPUT');
    // The switch's own label still names the switch input.
    expect(screen.getByRole('switch', { name: 'Flushed' })).toBeTruthy();
    for (const term of ['ec', 'ph', 'runoff']) {
      expect(helpButton(term).closest('label')).toBeNull();
    }
  });

  it('puts the trigger in the tab order right after its field', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText('EC'));
    await user.tab();
    expect(document.activeElement).toBe(helpButton('ec'));
    await user.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('pH note'));
  });

  it('opens the glossary tooltip on a click/tap of the trigger', async () => {
    renderWithProviders(<TestForm />);
    await act(async () => {
      fireEvent.click(helpButton('ec'));
    });
    const tooltip = await screen.findByRole('tooltip');
    expect(within(tooltip).getByText(short('ec'))).toBeTruthy();
  });

  it('does not toggle the switch when its help trigger is activated', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const toggle = screen.getByRole('switch', { name: 'Flushed' });
    await user.click(helpButton('runoff'));
    expect(toggle).not.toBeChecked();
    await user.click(screen.getByText('Flushed'));
    expect(toggle).toBeChecked();
  });
});
