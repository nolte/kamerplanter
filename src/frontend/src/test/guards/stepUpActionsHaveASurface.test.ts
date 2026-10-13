import { describe, expect, it } from 'vitest';
import { STEP_UP_ACTIONS } from '@/utils/stepUpReauth';

/**
 * #1906 — every act the backend asks a step-up for has a place in the UI that performs it.
 *
 * `oidc_provider_change` was a step-up act (#1883) with **no page**: the API enforced
 * it and nothing in the interface could present the dialog, so the only way to manage a
 * provider was a hand-made request — and the user guide said so in an info box. The class is
 * "an act in the `StepUpAction` union that no `<StepUpConfirmDialog stepUpAction=…>` names":
 * the type check passes (the union and both `Record`s are complete), the backend is guarded,
 * and the surface is simply absent.
 *
 * The inventory is the union itself (`STEP_UP_ACTIONS`, a `Record` over it), the surface is
 * a production source that names the act as the `stepUpAction` prop **or** in a
 * `stepUpAction: '…'` / `action: '…'` position handed to such a dialog. Writings covered: the
 * attribute with a string literal, with a braced literal, and a constant object field.
 * Not covered (and nothing writes it): an action computed at runtime.
 *
 * Acts that deliberately have no dialog are listed in {@link NO_DIALOG} with the measured
 * reason — an allow-list that must stay true (second assertion), not a place to park debts.
 */
const SOURCES = import.meta.glob(
  ['/src/pages/**/*.tsx', '/src/components/**/*.tsx', '/src/hooks/**/*.ts', '/src/hooks/**/*.tsx'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

/** Acts without a confirmation dialog of their own, each with the reason. */
const NO_DIALOG: Readonly<Record<string, string>> = {
  // `changeMemberRole` in `api/endpoints/tenants.ts` carries the step-up body (#2032), but the
  // tenant settings page offers no role control: the endpoint has no caller. Measured 2026-10-04.
  tenant_member_role_change: 'no UI control calls changeMemberRole (tenants.ts); API-only today',
  // #2137 — the service-account routes (`/t/{slug}/service-accounts`) have no page yet; REQ-023 §5b.0
  // records the frontend (§5b.10) as open. Measured 2026-10-05: no endpoint module calls them.
  service_account_change: 'service accounts are API-only today (REQ-023 §5b.0, frontend §5b.10 open)',
};

function surfacesOf(action: string): string[] {
  const writings = [
    new RegExp(`stepUpAction=\\{?\\s*['"]${action}['"]`),
    new RegExp(`stepUpAction:\\s*['"]${action}['"]`),
  ];
  return Object.entries(SOURCES)
    .filter(([, source]) => writings.some((re) => re.test(source)))
    .map(([path]) => path);
}

describe('step-up acts ↔ surfaces (#1906)', () => {
  it('reads the inventory and the sources (non-vacuity)', () => {
    expect(STEP_UP_ACTIONS.length).toBeGreaterThanOrEqual(15);
    expect(Object.keys(SOURCES).length).toBeGreaterThan(100);
    // The reader finds a writing it is known to exist in.
    expect(surfacesOf('tenant_deletion').length).toBeGreaterThan(0);
  });

  it.each(STEP_UP_ACTIONS.map((a) => [a]))('"%s" is performed by a dialog in the UI', (action) => {
    if (action in NO_DIALOG) return;
    expect(surfacesOf(action), `no page or component names stepUpAction "${action}"`).not.toEqual([]);
  });

  it('keeps the allow-list truthful: an act listed as dialog-less has none', () => {
    for (const action of Object.keys(NO_DIALOG)) {
      expect(surfacesOf(action), `"${action}" has a dialog now — delete its NO_DIALOG entry`).toEqual([]);
    }
  });
});
