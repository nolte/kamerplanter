/**
 * When the bed list under the plan fetches again (#2813): on every plan load **and** on every save.
 *
 * A save adopts the server's `plan_revision`, so a bed the editor created or duplicated exists on the server from
 * that moment; the list must not wait for the next plan load to show it.
 */
export function bedListReloadToken(loadRequestId: string | null, planRevision: number | null): string | null {
  if (loadRequestId === null) return null;
  return planRevision === null ? loadRequestId : `${loadRequestId}#${planRevision}`;
}
