import type { ModuleVisibilityState } from '@/api/types';

/**
 * REQ-042 / REQ-027 — localStorage persistence of module visibility overrides
 * for anonymous Light-mode users (no server-side user_preferences record).
 */

const KEY = 'kp-module-visibility';

export function readLocalModuleVisibility(): Record<string, ModuleVisibilityState> {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      return parsed as Record<string, ModuleVisibilityState>;
    }
    return {};
  } catch {
    return {};
  }
}

export function writeLocalModuleVisibility(
  value: Record<string, ModuleVisibilityState>,
): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // Storage unavailable (private mode / quota) — ignore silently.
  }
}

export function clearLocalModuleVisibility(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
