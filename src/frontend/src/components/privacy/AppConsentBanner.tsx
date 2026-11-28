import { lazy, Suspense } from 'react';
import { isBrowserConsentManaged } from '@/observability/errorTracking';

// #3023 — the banner (and its Switch controls) is its own chunk: most deployments suppress it, and where it
// shows, it shows once per browser and account. The shell does not wait for it. A chunk that fails to load
// renders nothing instead of throwing into the shell's error boundary: without the banner nobody is asked,
// and nothing is sent without an answer (UI-NFR-013 §5.4).
const ConsentBanner = lazy(() =>
  import('@/components/privacy/ConsentBanner').catch((error: unknown) => {
    console.warn('[consent] banner failed to load', error);
    return { default: () => null };
  }),
);

/**
 * The app-shell mount of the consent banner (UI-NFR-013 CB-001, #2159, #3025).
 *
 * Suppressed in two cases (`isBrowserConsentManaged`):
 *
 * - **Light mode** (REQ-027): the GDPR household exemption waives the consent
 *   requirement. The browser tracker is off there independently of this
 *   banner (`trackingPermitted` in `observability/errorTracking.ts`), so a
 *   grant stored before a full -> light switch does not start it either.
 * - **No error-tracking DSN**: browser error reports are the only processing
 *   this banner's decision switches; without a DSN it would collect a decision
 *   with no effect.
 *
 * Which form shows (device / account) and when is decided inside the banner by
 * `consentPrompt`; who is signed in comes from `consentAuthBridge.ts`.
 */
export default function AppConsentBanner() {
  if (!isBrowserConsentManaged()) return null;
  return (
    <Suspense fallback={null}>
      <ConsentBanner />
    </Suspense>
  );
}
