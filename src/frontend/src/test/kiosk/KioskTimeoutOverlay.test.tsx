/**
 * #3017 (W-07) — the kiosk timeout warning announced its countdown through `aria-live="assertive"` on the
 * visible number, i.e. every second, interrupting everything else a screen reader had to say.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import i18n from 'i18next';
import KioskTimeoutOverlay from '@/components/kiosk/KioskTimeoutOverlay';
import { expectNoA11yViolations } from '../a11y/expectNoA11yViolations';

const countdown = (seconds: number) => i18n.t('pages.kiosk.timeout.countdown', { seconds });

describe('KioskTimeoutOverlay (#3017)', () => {
  it('moves focus to "continue" on open and keeps it inside the alertdialog', async () => {
    const user = userEvent.setup();
    render(
      <>
        <button type="button">behind</button>
        <KioskTimeoutOverlay open remainingSeconds={30} onContinue={vi.fn()} />
      </>,
    );
    const dialog = screen.getByRole('alertdialog');
    const resume = screen.getByTestId('kiosk-timeout-continue');
    expect(resume).toHaveFocus();
    await user.tab();
    expect(dialog.contains(document.activeElement)).toBe(true);
    // The opening reads the countdown once, through the dialog's description.
    expect(dialog).toHaveAccessibleDescription(countdown(30));
  });

  it('does not announce every tick — only every tenth second and the last five, politely', () => {
    const { rerender } = render(<KioskTimeoutOverlay open remainingSeconds={30} onContinue={vi.fn()} />);
    expect(document.querySelector('[aria-live="assertive"]')).toBeNull();

    const region = screen.getByTestId('kiosk-timeout-announcement');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toHaveTextContent(countdown(30));

    for (const seconds of [29, 28, 21]) {
      rerender(<KioskTimeoutOverlay open remainingSeconds={seconds} onContinue={vi.fn()} />);
      // The visible number ticks …
      expect(screen.getByText(countdown(seconds))).toBeInTheDocument();
      // … the spoken text does not.
      expect(region).toHaveTextContent(countdown(30));
    }
    rerender(<KioskTimeoutOverlay open remainingSeconds={20} onContinue={vi.fn()} />);
    expect(region).toHaveTextContent(countdown(20));
    rerender(<KioskTimeoutOverlay open remainingSeconds={5} onContinue={vi.fn()} />);
    expect(region).toHaveTextContent(countdown(5));
  });

  it('returns focus to the control that had it once the user continues', async () => {
    const user = userEvent.setup();
    const Harness = ({ open }: { open: boolean }) => (
      <>
        <button type="button">trigger</button>
        <KioskTimeoutOverlay open={open} remainingSeconds={30} onContinue={vi.fn()} />
      </>
    );
    const { rerender } = render(<Harness open={false} />);
    const trigger = screen.getByRole('button', { name: 'trigger' });
    trigger.focus();
    rerender(<Harness open />);
    expect(screen.getByTestId('kiosk-timeout-continue')).toHaveFocus();
    await user.click(screen.getByTestId('kiosk-timeout-continue'));
    rerender(<Harness open={false} />);
    expect(trigger).toHaveFocus();
  });

  it('has no serious accessibility violations', async () => {
    render(<KioskTimeoutOverlay open remainingSeconds={30} onContinue={vi.fn()} />);
    await expectNoA11yViolations(screen.getByRole('alertdialog'), { minImpact: 'serious' });
  });
});
