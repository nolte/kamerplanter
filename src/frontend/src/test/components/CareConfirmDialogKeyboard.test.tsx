/**
 * #3017 (A-07) — the feeding-details section of the care confirm dialog is opened and closed from the
 * keyboard through its named disclosure button, which says what it controls; Escape closes the dialog.
 */
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import i18n from 'i18next';
import CareConfirmDialog from '@/pages/pflege/components/CareConfirmDialog';
import type { Fertilizer } from '@/api/types';
import { renderWithProviders } from '../helpers';

const fertilizer = { key: 'f1', product_name: 'BioGrow', brand: 'BioBizz' } as Fertilizer;

function renderDialog(onClose = vi.fn()) {
  renderWithProviders(
    <CareConfirmDialog
      open
      onClose={onClose}
      onConfirm={vi.fn()}
      plantName="Basil"
      reminderType="watering"
      availableFertilizers={[fertilizer]}
    />,
  );
  return { onClose };
}

describe('CareConfirmDialog keyboard operation (#3017)', () => {
  it('toggles the feeding details with Enter and Space on the disclosure button', async () => {
    const user = userEvent.setup();
    renderDialog();

    const toggle = screen.getByTestId('care-confirm-feeding-toggle');
    expect(toggle).toHaveAccessibleName(i18n.t('pages.pflege.expandFeedingDetails'));
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    const region = document.getElementById(toggle.getAttribute('aria-controls') ?? '');
    expect(region).not.toBeNull();

    toggle.focus();
    await user.keyboard('{Enter}');
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(toggle).toHaveAccessibleName(i18n.t('pages.pflege.collapseFeedingDetails'));
    expect(screen.getByTestId('confirm-volume-field')).toBeVisible();

    await user.keyboard(' ');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(toggle).toHaveFocus();
  });

  it('keeps focus inside the dialog and closes it on Escape', async () => {
    const user = userEvent.setup();
    const { onClose } = renderDialog();
    const dialog = screen.getByRole('dialog');
    await user.tab();
    expect(dialog.contains(document.activeElement)).toBe(true);
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalled();
  });
});
