/**
 * Click classification for surfaces that are real links (#3047).
 *
 * On a real `<a href>` the browser follows the link in the current tab only for a plain primary click.
 * Ctrl/Cmd/Shift + click and a middle click open the target in a new tab or window and leave this tab
 * where it is — so a popover or drawer around the link must stay open for those. A right click
 * (`button === 2`) opens the context menu and is no activation at all.
 */

/** The subset of a mouse event the classification reads (React and DOM events both fit). */
export interface ClickLike {
  button: number;
  ctrlKey: boolean;
  metaKey: boolean;
  shiftKey: boolean;
  altKey: boolean;
}

/** True for a click that follows a link in the current tab: primary button, no modifier key. */
export function isPlainPrimaryClick(e: ClickLike): boolean {
  return e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey;
}

/** True for a click that activates a link at all — primary or middle button; a right click is not one. */
export function isLinkActivation(e: ClickLike): boolean {
  return e.button === 0 || e.button === 1;
}
