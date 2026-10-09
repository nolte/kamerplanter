import ConsentBanner from '@/components/privacy/ConsentBanner';
import { isLightMode } from '@/config/mode';
import { isErrorTrackingConfigured } from '@/observability/errorTracking';

/**
 * The app-shell mount of the consent banner (UI-NFR-013 CB-001, #2159).
 *
 * Suppressed in two cases:
 *
 * - **Light mode** (REQ-027): the GDPR household exemption waives the consent
 *   requirement. The browser tracker is off there independently of this
 *   banner (`trackingPermitted` in `observability/errorTracking.ts`), so a
 *   grant stored before a full -> light switch does not start it either.
 * - **No error-tracking DSN**: browser error tracking is the only processing
 *   this banner's decision switches. `external_services` is read by nothing
 *   since REQ-025 v1.31 (#2136), and the banner does not sync to the REQ-025
 *   ConsentEngine yet, so without a DSN it would collect a decision with no
 *   effect. Once another browser-side category or the backend sync lands, this
 *   gate widens to "any category the decision switches is configured".
 */
export default function AppConsentBanner() {
  return <ConsentBanner suppress={isLightMode || !isErrorTrackingConfigured()} />;
}
