import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import FormActions from '@/components/form/FormActions';
import '@/i18n';

function renderComponent(props: Partial<Parameters<typeof FormActions>[0]> = {}) {
  const defaults = { onCancel: vi.fn() };
  const merged = { ...defaults, ...props };
  return {
    ...merged,
    ...render(
      <ThemeContextProvider>
        <SnackbarProvider>
          <FormActions {...merged} />
        </SnackbarProvider>
      </ThemeContextProvider>,
    ),
  };
}

describe('FormActions', () => {
  it('renders cancel and save buttons', () => {
    renderComponent();
    expect(screen.getByRole('button', { name: /abbrechen|cancel/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /speichern|save/i })).toBeTruthy();
  });

  it('calls onCancel when cancel clicked', async () => {
    const user = userEvent.setup();
    const { onCancel } = renderComponent();
    await user.click(screen.getByRole('button', { name: /abbrechen|cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('uses custom save label', () => {
    renderComponent({ saveLabel: 'Create' });
    expect(screen.getByRole('button', { name: 'Create' })).toBeTruthy();
  });

  it('disables buttons when loading', () => {
    renderComponent({ loading: true });
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it('submit button has type submit', () => {
    renderComponent();
    const saveBtn = screen.getByRole('button', { name: /speichern|save/i });
    expect(saveBtn).toHaveAttribute('type', 'submit');
  });
});
