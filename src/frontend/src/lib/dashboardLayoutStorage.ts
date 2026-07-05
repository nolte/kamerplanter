import type { DashboardLayout } from '@/api/types';

/**
 * REQ-045 / REQ-027 — localStorage persistence of the personalized dashboard
 * layout for anonymous Light-mode users (no server-side user_preferences
 * record), plus the one-time personalization coachmark flag (U-005).
 */

const KEY = 'kp-dashboard-layout';
const HINT_KEY = 'dashboard_personalization_hint_dismissed';

export function readLocalDashboardLayout(): DashboardLayout | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') return parsed as DashboardLayout;
    return null;
  } catch {
    return null;
  }
}

export function writeLocalDashboardLayout(value: DashboardLayout | null): void {
  try {
    if (value === null) {
      localStorage.removeItem(KEY);
      return;
    }
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // Storage unavailable (private mode / quota) — ignore silently.
  }
}

export function clearLocalDashboardLayout(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}

// ── First-use coachmark (U-005) ──────────────────────────────────────
export function isPersonalizationHintDismissed(): boolean {
  try {
    return localStorage.getItem(HINT_KEY) === 'true';
  } catch {
    return true; // storage unavailable → don't nag
  }
}

export function dismissPersonalizationHint(): void {
  try {
    localStorage.setItem(HINT_KEY, 'true');
  } catch {
    // ignore
  }
}
