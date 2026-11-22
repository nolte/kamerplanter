/**
 * The tooltip of a button that opens a menu in the editor (REQ-053 §17.3, GP-UX-010/066, #2904): the header bar's
 * overflow "⋮", the sub-menu buttons of the tool bar, "Align" and the panel's "⋯".
 *
 * A plain MUI tooltip on such a button outlives its menu: the menu's backdrop sits between the pointer and the
 * button, so when the menu closes the pointer that pressed the button is "over" it again and opens the tooltip, and
 * the focus the menu hands back opens it too (keyboard modality). On the phone it then covers the bottom sheet's tabs
 * and its close button. This one is controlled:
 *
 * - it is never shown while the menu is open;
 * - after the menu closed, neither the returned focus nor a pointer that has not moved since it pressed the button
 *   brings it back: the focus has to leave the button once, the pointer has to move or leave;
 * - otherwise it behaves like every tooltip (hover and keyboard focus open it, leave and blur close it).
 */
import { useRef, useState, type FocusEvent, type PointerEvent, type SyntheticEvent } from 'react';
import Tooltip, { type TooltipProps } from '@mui/material/Tooltip';

export interface MenuTriggerTooltipProps extends Omit<TooltipProps, 'open' | 'onOpen' | 'onClose'> {
  /** Whether the menu of the wrapped button is open. */
  menuOpen: boolean;
}

const NOT_MUTED = { focus: false, hover: false } as const;
const MUTED = { focus: true, hover: true } as const;

export function MenuTriggerTooltip({
  menuOpen,
  onPointerDown,
  onPointerMove,
  onPointerLeave,
  onBlur,
  ...tooltip
}: MenuTriggerTooltipProps) {
  const [open, setOpen] = useState(false);
  // What may not open the tooltip right after the menu closed: the focus it hands back, the pointer that pressed.
  const [muted, setMuted] = useState<{ focus: boolean; hover: boolean }>(NOT_MUTED);
  const [menuWasOpen, setMenuWasOpen] = useState(menuOpen);
  // Where the pointer pressed the button (null: opened by keyboard); a move away from it is a hover of its own.
  const pressedAt = useRef<{ x: number; y: number } | null>(null);
  if (menuWasOpen !== menuOpen) {
    // Adjusted while rendering: no frame with the tooltip over the menu or the sheet.
    setMenuWasOpen(menuOpen);
    setOpen(false);
    setMuted(menuOpen ? NOT_MUTED : MUTED);
  }

  const handleOpen = (event: SyntheticEvent) => {
    if (menuOpen) return;
    if (event.type === 'focus' ? muted.focus : muted.hover) return;
    setOpen(true);
  };

  return (
    <Tooltip
      {...tooltip}
      open={open && !menuOpen}
      onOpen={handleOpen}
      onClose={() => setOpen(false)}
      onPointerDown={(event: PointerEvent<HTMLDivElement>) => {
        pressedAt.current = { x: event.clientX, y: event.clientY };
        onPointerDown?.(event);
      }}
      onPointerMove={(event: PointerEvent<HTMLDivElement>) => {
        const at = pressedAt.current;
        const moved = at === null || at.x !== event.clientX || at.y !== event.clientY;
        if (!menuOpen && muted.hover && event.pointerType !== 'touch' && moved) {
          setMuted((previous) => ({ ...previous, hover: false }));
          setOpen(true);
        }
        onPointerMove?.(event);
      }}
      onPointerLeave={(event: PointerEvent<HTMLDivElement>) => {
        if (!menuOpen && muted.hover) setMuted((previous) => ({ ...previous, hover: false }));
        onPointerLeave?.(event);
      }}
      onBlur={(event: FocusEvent<HTMLDivElement>) => {
        // The focus moving into the open menu is no "left the button" yet.
        if (!menuOpen && muted.focus) setMuted((previous) => ({ ...previous, focus: false }));
        onBlur?.(event);
      }}
    />
  );
}
