import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { SnackbarProvider } from 'notistack';
import Button from '@mui/material/Button';
import { useNotification } from '@/hooks/useNotification';
import i18n from '@/i18n/i18n';

/**
 * #3013 (N-10, UI-NFR-004) — a toast can be dismissed by keyboard instead of only by waiting out
 * its timeout. `useNotification` attaches the close button to every toast it shows.
 */
function Trigger() {
  const notification = useNotification();
  return <Button onClick={() => notification.error('Speichern fehlgeschlagen')}>raise</Button>;
}

describe('snackbar close action (#3013)', () => {
  it('dismisses an error toast with the keyboard', async () => {
    const user = userEvent.setup();
    render(
      <SnackbarProvider>
        <Trigger />
      </SnackbarProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'raise' }));
    expect(await screen.findByText('Speichern fehlgeschlagen')).toBeInTheDocument();

    const close = screen.getByRole('button', { name: i18n.t('common.close') });
    close.focus();
    expect(close).toHaveFocus();
    await user.keyboard('{Enter}');

    await waitFor(() => expect(screen.queryByText('Speichern fehlgeschlagen')).toBeNull());
  });
});
