/**
 * Which element a key of the plan editor came from (REQ-053 GP-NFR-020/068, GP-FR-010): a key typed into a field
 * belongs to the field, a key on a control (button, tab, menu item) activates the control.
 */

/** An editable host and what lies inside it (the attribute as well: not every DOM implements `isContentEditable`). */
const CONTENT_EDITABLE = '[contenteditable]:not([contenteditable="false"])';

/** A text field, a native select or a contenteditable: every printable key - Space included - is typed there. */
export function isTextEntry(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (/^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName) ||
      target.isContentEditable ||
      target.closest(CONTENT_EDITABLE) !== null)
  );
}

/**
 * Controls that act on Space themselves (WAI-ARIA: button, tab, menu item, check box, switch, ...). A plan object is
 * a `role="button"` too, but it is part of the drawing, not of the chrome: see {@link isPanModifierTarget}.
 */
const SPACE_CONTROLS = [
  'button',
  'a[href]',
  'summary',
  '[role="button"]',
  '[role="link"]',
  '[role="tab"]',
  '[role="menuitem"]',
  '[role="menuitemcheckbox"]',
  '[role="menuitemradio"]',
  '[role="checkbox"]',
  '[role="radio"]',
  '[role="switch"]',
  '[role="option"]',
  '[role="combobox"]',
  '[role="listbox"]',
  '[role="slider"]',
  '[role="spinbutton"]',
  '[role="treeitem"]',
].join(', ');

/** Marks a drawn plan object (both renderers); its Space activation waits for the release. */
const PLAN_OBJECT = '[data-plan-key]';

/**
 * Space held down on `target` makes a primary-button drag on the canvas `surface` pan (GP-FR-010). It does so on the
 * surface itself, on a drawn plan object (which activates on the release of Space, and only when no pan used it) and
 * on any other non-interactive part of the surface. It does not on a text field (Space types a space), on a control
 * (Space activates it) or on anything outside the surface's DOM (a menu or dialog in a portal bubbles through the
 * React tree but is not part of the canvas).
 */
export function isPanModifierTarget(target: EventTarget | null, surface: Element): boolean {
  if (!(target instanceof Element) || !surface.contains(target)) return false;
  if (target === surface) return true;
  if (isTextEntry(target)) return false;
  if (target.matches(PLAN_OBJECT)) return true;
  const control = target.closest(SPACE_CONTROLS);
  return control === null || !surface.contains(control);
}
