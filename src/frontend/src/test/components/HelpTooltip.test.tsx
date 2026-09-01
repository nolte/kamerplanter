import { describe, it, expect, vi } from 'vitest';
import { fireEvent, screen } from '@testing-library/react';
import Form from '@/components/form/Form';
import HelpTooltip from '@/components/common/HelpTooltip';
import { renderWithProviders } from '@/test/helpers';

/** The trigger button that owns the glossary icon for `term`. */
function triggerFor(term: string): HTMLElement {
  const button = screen.getByTestId(`help-tooltip-icon-${term}`).closest('button');
  if (!button) throw new Error(`no <button> trigger around the ${term} glossary icon`);
  return button;
}

describe('HelpTooltip', () => {
  it('renders the trigger icon for a known glossary term', () => {
    renderWithProviders(
      <HelpTooltip term="ec">
        <span>EC (mS/cm)</span>
      </HelpTooltip>,
    );
    expect(screen.getByTestId('help-tooltip-icon-ec')).toBeTruthy();
    expect(screen.getByText('EC (mS/cm)')).toBeTruthy();
  });

  it('renders icon-only mode without children', () => {
    renderWithProviders(<HelpTooltip term="ph" iconOnly />);
    expect(screen.getByTestId('help-tooltip-icon-ph')).toBeTruthy();
  });

  it('still renders an icon for an unknown term (graceful fallback)', () => {
    renderWithProviders(<HelpTooltip term="totally-unknown" iconOnly />);
    expect(screen.getByTestId('help-tooltip-icon-totally-unknown')).toBeTruthy();
  });

  // #1290. The predecessor of this test asserted `tabindex="0"` on the wrapper,
  // which the old span satisfied while ARIA discarded its accessible name — the
  // assertion was true of an element no screen reader could announce. What the
  // trigger owes is a role AND a name, so that is what is asserted here.
  it('exposes the trigger as a button carrying an accessible name', () => {
    renderWithProviders(<HelpTooltip term="vpd" iconOnly />);
    const trigger = triggerFor('vpd');
    expect(trigger.tagName).toBe('BUTTON');
    // Native <button> is focusable without an explicit tabindex; re-adding one
    // would be the hand-rolled shape this fix removed.
    expect(trigger.getAttribute('tabindex')).toBeNull();
    expect(trigger.getAttribute('aria-label')?.trim()).toBeTruthy();
  });

  it('keeps its children and still exposes a named button in the labelled variant', () => {
    renderWithProviders(
      <HelpTooltip term="vpd">
        <span>VPD</span>
      </HelpTooltip>,
    );
    expect(screen.getByText('VPD')).toBeTruthy();
    const trigger = triggerFor('vpd');
    expect(trigger.tagName).toBe('BUTTON');
    expect(trigger.getAttribute('aria-label')?.trim()).toBeTruthy();
    // The label wrapper must NOT be a second focus stop: one control, one stop.
    const wrapper = screen.getByText('VPD').parentElement;
    expect(wrapper?.getAttribute('tabindex')).toBeNull();
  });

  // A <button> inside a <form> defaults to type="submit". Several call sites put
  // this trigger next to a field, so the default would submit the form on every
  // help click. Asserted rather than trusted.
  it('declares type="button" so it cannot submit a surrounding form', () => {
    const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault());
    renderWithProviders(
      <Form onSubmit={onSubmit}>
        <HelpTooltip term="ph" iconOnly />
      </Form>,
    );
    const trigger = triggerFor('ph');
    expect(trigger.getAttribute('type')).toBe('button');
    fireEvent.click(trigger);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  // Issue #439 contract: this trigger can sit inside an ancestor navigation
  // link, and activating it must not navigate. Both halves are asserted,
  // because `stopPropagation` alone was measured NOT to deliver it — an <a>
  // follows its href as the click's *default action*, which propagation control
  // never touches.
  it('does not let an activation reach an ancestor link (#439)', () => {
    const ancestorClick = vi.fn();
    renderWithProviders(
      <a href="/pflanzenschutz/pests" onClick={ancestorClick}>
        <HelpTooltip term="ph" iconOnly />
      </a>,
    );
    const notCancelled = fireEvent.click(triggerFor('ph'));
    expect(ancestorClick).not.toHaveBeenCalled();
    // fireEvent returns false when the event was cancelled, i.e. preventDefault
    // ran — which is what stops the browser following the ancestor's href.
    expect(notCancelled).toBe(false);
  });
});
