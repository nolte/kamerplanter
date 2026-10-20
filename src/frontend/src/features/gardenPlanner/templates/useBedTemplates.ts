/**
 * The bed templates the user can pick (REQ-053 GP-FR-044/045): the system templates (standard sizes) and the
 * tenant's own. Loaded on demand - only while the picker or the standard-size choice is open - so the editor
 * makes no request of its own otherwise. `reload` refreshes the list after "Save as template".
 */
import { useCallback, useEffect, useState } from 'react';
import { listBedTemplates } from '../api/gardenPlan';
import type { BedTemplate } from '../model/types';

export interface BedTemplates {
  templates: BedTemplate[];
  loading: boolean;
  failed: boolean;
  reload: () => void;
}

export function useBedTemplates(enabled: boolean): BedTemplates {
  const [templates, setTemplates] = useState<BedTemplate[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [round, setRound] = useState(0);
  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    listBedTemplates()
      .then((all) => {
        if (cancelled) return;
        setTemplates(all);
        setFailed(false);
      })
      .catch(() => {
        if (cancelled) return;
        setFailed(true);
        setTemplates((previous) => previous ?? []);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, round]);
  const reload = useCallback(() => setRound((n) => n + 1), []);
  return { templates: templates ?? [], loading: enabled && templates === null, failed, reload };
}
