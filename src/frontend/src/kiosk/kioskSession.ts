import { useEffect, useSyncExternalStore } from 'react';

/**
 * UI-NFR-019 §2.6 — the two facts the kiosk timeout needs from the forms of the page, kept in one
 * tiny store so neither the forms nor the shell import each other:
 *
 * - **Unsaved input** (R-038): every form that guards its own input (`UnsavedChangesGuard` on a
 *   page, `FormDialog` around a dialog form) reports while it is dirty. The warning overlay then
 *   says that the input will be discarded — the "Nutzer MUSS gewarnt werden" branch of R-038.
 * - **The kiosk reset** (R-035): the return to the start page after the warning must not be
 *   stoppable. `UnsavedChangesGuard` blocks navigation while dirty; during a reset it lets it pass,
 *   so the next person never finds the previous person's input on screen.
 */

const dirtyForms = new Set<symbol>();
const listeners = new Set<() => void>();
let resetting = false;

function emit() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function hasUnsavedInput(): boolean {
  return dirtyForms.size > 0;
}

/** A form reports here while it holds input the user has not saved. */
export function useReportUnsavedInput(dirty: boolean): void {
  useEffect(() => {
    if (!dirty) return;
    const token = Symbol('dirty-form');
    dirtyForms.add(token);
    emit();
    return () => {
      dirtyForms.delete(token);
      emit();
    };
  }, [dirty]);
}

/** Whether any mounted form currently holds unsaved input. */
export function useHasUnsavedInput(): boolean {
  return useSyncExternalStore(subscribe, hasUnsavedInput, hasUnsavedInput);
}

/** Whether the kiosk timeout is returning to the start page right now. */
export function isKioskResetting(): boolean {
  return resetting;
}

/**
 * Run the kiosk reset navigation with the unsaved-changes guards stood down. The flag holds until
 * the navigation has settled (a data-router `navigate` returns a promise), then clears.
 */
export function runKioskReset(navigate: () => void | Promise<void>): void {
  resetting = true;
  let pending: void | Promise<void>;
  try {
    pending = navigate();
  } catch (error) {
    resetting = false;
    throw error;
  }
  void Promise.resolve(pending).finally(() => {
    resetting = false;
  });
}
