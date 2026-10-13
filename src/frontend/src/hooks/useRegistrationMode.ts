import { useEffect, useMemo, useState } from 'react';
import { getMode } from '@/api/endpoints/mode';
import type { RegistrationMode } from '@/api/types';

export interface RegistrationModeState {
  /** The instance's registration mode; `null` while loading. */
  mode: RegistrationMode | null;
  /** Whether an e-mail domain allowlist applies to registration. */
  domainRestricted: boolean;
  /** `GET /mode` failed: the pages fall back to `open` and let the backend decide (it refuses with 403). */
  failed: boolean;
}

/**
 * The registration mode of this instance (#2132), read once from `GET /mode`.
 *
 * Only a hint for the UI — the backend enforces the mode on `POST /auth/register`
 * and on the first OIDC sign-in whatever this says. A failed read therefore falls
 * back to showing the form (`open`) rather than hiding registration on a hiccup.
 */
export function useRegistrationMode(): RegistrationModeState {
  const [mode, setMode] = useState<RegistrationMode | null>(null);
  const [domainRestricted, setDomainRestricted] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    getMode()
      .then((response) => {
        if (!active) return;
        setMode(response.registration?.mode ?? 'open');
        setDomainRestricted(response.registration?.domain_restricted ?? false);
      })
      .catch(() => {
        if (!active) return;
        setFailed(true);
        setMode('open');
      });
    return () => {
      active = false;
    };
  }, []);

  return useMemo(() => ({ mode, domainRestricted, failed }), [mode, domainRestricted, failed]);
}
