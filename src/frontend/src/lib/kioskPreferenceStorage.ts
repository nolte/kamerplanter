/**
 * UI-NFR-019 R-002 — localStorage persistence of the kiosk-mode flags.
 *
 * The kiosk preference must survive a reload even for anonymous Light-mode
 * users (REQ-027), who have no server-side ``user_preferences`` record. In Full
 * mode localStorage additionally acts as a fast, reload-free cache so the kiosk
 * shell renders instantly before the server preference has been fetched; the
 * server copy is reconciled once it arrives.
 */

export interface KioskPreference {
  kiosk_enabled: boolean;
  high_contrast: boolean;
}

const KEY = 'kp-kiosk-preference';

export const defaultKioskPreference: KioskPreference = {
  kiosk_enabled: false,
  high_contrast: false,
};

/** Whether the user has ever explicitly set a kiosk preference on this device. */
export function hasLocalKioskPreference(): boolean {
  try {
    return localStorage.getItem(KEY) !== null;
  } catch {
    return false;
  }
}

export function readLocalKioskPreference(): KioskPreference {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...defaultKioskPreference };
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      return {
        kiosk_enabled: Boolean((parsed as KioskPreference).kiosk_enabled),
        high_contrast: Boolean((parsed as KioskPreference).high_contrast),
      };
    }
    return { ...defaultKioskPreference };
  } catch {
    return { ...defaultKioskPreference };
  }
}

export function writeLocalKioskPreference(value: KioskPreference): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // Storage unavailable (private mode / quota) — ignore silently.
  }
}

export function clearLocalKioskPreference(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
