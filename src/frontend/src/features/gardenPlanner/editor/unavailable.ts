/**
 * A button of the editor that cannot act right now but keeps the keyboard focus (REQ-053 GP-NFR-070, WCAG 2.2
 * SC 2.4.3): `aria-disabled` instead of `disabled`. A `disabled` button drops the focus to the page body the moment it
 * turns disabled under the cursor - "Save" right after a save, undo at the start of the history, zoom-out at the
 * fit zoom, "Finish" once the shape is done. With `aria-disabled` the button stays focusable and in a tool bar's
 * roving order (WAI-ARIA "Toolbar"), screen readers still say "unavailable", and the MUI state class gives it the
 * theme's disabled look (and `pointer-events: none`, so the tooltip is carried by the wrapping span as before).
 *
 * The caller passes no click handler while the button is unavailable: a press does nothing.
 */
import { buttonBaseClasses } from '@mui/material/ButtonBase';

export interface UnavailableProps {
  'aria-disabled'?: true;
  className?: string;
}

export function unavailableProps(unavailable: boolean): UnavailableProps {
  return unavailable ? { 'aria-disabled': true, className: buttonBaseClasses.disabled } : {};
}
