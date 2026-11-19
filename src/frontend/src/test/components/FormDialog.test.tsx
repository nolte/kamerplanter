import { render, screen, waitFor, within, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SnackbarProvider } from 'notistack';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import i18n from 'i18next';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import { ThemeContextProvider } from '@/theme';
import FormDialog from '@/components/form/FormDialog';
import FormDialogCancelButton from '@/components/form/FormDialogCancelButton';
import Form from '@/components/form/Form';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import { useDialogForm } from '@/hooks/useDialogForm';
import { useFormFieldViolations } from '@/hooks/useFieldViolations';
import { useApiError } from '@/hooks/useApiError';
import { ApiError } from '@/api/errors';
import '@/i18n';

/**
 * #3019 — the dialog form contract: dirty guard on every close path,
 * `mode: 'onBlur'`, and 422 field violations on the fields.
 */

const schema = z.object({
  name: z.string().min(1, 'required-name'),
  notes: z.string(),
});
type Values = z.infer<typeof schema>;

const ENGLISH_REASON = 'String should have at least 3 characters';

function violationError(details: { field: string; code: string }[]): ApiError {
  return new ApiError(
    {
      error_id: 'err_test',
      error_code: 'VALIDATION_ERROR',
      message: 'Request validation failed',
      details: details.map((d) => ({ ...d, reason: ENGLISH_REASON })),
      timestamp: '2026-11-18T00:00:00Z',
      path: '/api/v1/t/test/things',
      method: 'POST',
    },
    422,
  );
}

interface HarnessProps {
  onClose: () => void;
  onSubmit?: (values: Values) => Promise<void>;
  customActions?: boolean;
}

function Harness({ onClose, onSubmit = async () => undefined, customActions = false }: HarnessProps) {
  const { handleError } = useApiError();
  const { control, handleSubmit } = useDialogForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', notes: '' },
  });
  const applyFieldViolation = useFormFieldViolations(control);
  const submit = async (values: Values) => {
    try {
      await onSubmit(values);
    } catch (err) {
      handleError(err, applyFieldViolation);
    }
  };
  return (
    <FormDialog control={control} open onClose={onClose} data-testid="harness-dialog">
      <DialogContent>
        <Form onSubmit={handleSubmit(submit)}>
          <FormTextField name="name" control={control} label="Name" />
          <FormTextField name="notes" control={control} label="Notes" />
          {customActions ? (
            <DialogActions>
              <FormDialogCancelButton onCancel={onClose} data-testid="custom-cancel" />
            </DialogActions>
          ) : (
            <FormActions onCancel={onClose} />
          )}
        </Form>
      </DialogContent>
    </FormDialog>
  );
}

function renderHarness(props: Partial<HarnessProps> = {}) {
  const onClose = vi.fn();
  render(
    <ThemeContextProvider>
      <SnackbarProvider>
        <Harness onClose={onClose} {...props} />
      </SnackbarProvider>
    </ThemeContextProvider>,
  );
  return { onClose, user: userEvent.setup() };
}

function nameInput(): HTMLInputElement {
  return within(screen.getByTestId('form-field-name')).getByRole('textbox') as HTMLInputElement;
}

describe('FormDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    cleanup();
  });

  it('closes a clean form at once on cancel, Escape and backdrop click', async () => {
    const { onClose, user } = renderHarness();

    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledTimes(1);

    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(2);

    // MUI renders the backdrop as the dialog container's previous sibling.
    const backdrop = document.querySelector('.MuiBackdrop-root') as HTMLElement;
    await user.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(3);
    expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument();
  });

  it('asks before a dirty form is discarded by the cancel button', async () => {
    const { onClose, user } = renderHarness();
    await user.type(nameInput(), 'Tomate');

    await user.click(screen.getByTestId('form-cancel-button'));

    const prompt = await screen.findByTestId('confirm-dialog');
    expect(within(prompt).getByText(i18n.t('common.discardChangesTitle'))).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('asks before a dirty form is discarded by Escape', async () => {
    const { onClose, user } = renderHarness();
    await user.type(nameInput(), 'Tomate');

    await user.keyboard('{Escape}');

    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('asks before a dirty form is discarded by a backdrop click', async () => {
    const { onClose, user } = renderHarness();
    await user.type(nameInput(), 'Tomate');

    const backdrop = document.querySelector('.MuiBackdrop-root') as HTMLElement;
    await user.click(backdrop);

    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('closes after the discard is confirmed', async () => {
    const { onClose, user } = renderHarness();
    await user.type(nameInput(), 'Tomate');
    await user.click(screen.getByTestId('form-cancel-button'));

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('keeps the input when the discard question is cancelled', async () => {
    const { onClose, user } = renderHarness();
    await user.type(nameInput(), 'Tomate');
    await user.click(screen.getByTestId('form-cancel-button'));

    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument());
    expect(onClose).not.toHaveBeenCalled();
    expect(nameInput().value).toBe('Tomate');
  });

  it('guards a custom cancel button in its own DialogActions too', async () => {
    const { onClose, user } = renderHarness({ customActions: true });
    await user.type(nameInput(), 'Tomate');

    await user.click(screen.getByTestId('custom-cancel'));

    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('validates a field when it loses focus, before any submit (mode onBlur)', async () => {
    const { user } = renderHarness();

    await user.click(nameInput());
    await user.tab();

    expect(await within(screen.getByTestId('form-field-name')).findByText('required-name')).toBeInTheDocument();
  });

  it('puts a 422 violation on its field in German and never shows the English reason', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      violationError([{ field: 'body.notes', code: 'string_too_short' }]),
    );
    const { user } = renderHarness({ onSubmit });
    await user.type(nameInput(), 'Tomate');

    await user.click(screen.getByTestId('form-submit-button'));

    const field = screen.getByTestId('form-field-notes');
    expect(await within(field).findByText(i18n.t('validation.invalid'))).toBeInTheDocument();
    expect(within(field).getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
    // The toast pairs with the generic "check your input" text.
    expect(await screen.findByText(i18n.t('errors.validation'))).toBeInTheDocument();
    expect(screen.queryByText(ENGLISH_REASON)).not.toBeInTheDocument();
  });

  it('translates a known violation code into its own field text', async () => {
    const onSubmit = vi.fn().mockRejectedValue(violationError([{ field: 'body.name', code: 'missing' }]));
    const { user } = renderHarness({ onSubmit });
    await user.type(nameInput(), 'Tomate');

    await user.click(screen.getByTestId('form-submit-button'));

    expect(
      await within(screen.getByTestId('form-field-name')).findByText(i18n.t('validation.required')),
    ).toBeInTheDocument();
  });

  it('leaves a violation on a field the form does not render to the toast', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      violationError([{ field: 'body.server_only', code: 'string_too_short' }]),
    );
    const { user } = renderHarness({ onSubmit });
    await user.type(nameInput(), 'Tomate');

    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.validation'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('validation.invalid'))).not.toBeInTheDocument();
    expect(screen.queryByText(ENGLISH_REASON)).not.toBeInTheDocument();
  });
});
