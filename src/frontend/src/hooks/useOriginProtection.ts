import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { DataOrigin } from '@/components/common/OriginChip';

interface UseOriginProtectionInput {
  origin?: DataOrigin;
  isSystem?: boolean;
}

export interface OriginProtection {
  /** Resolved origin marker. Returns 'tenant' if neither origin nor isSystem is set. */
  origin: DataOrigin;
  /** True if the record must not be edited (UI-NFR-018 R-027). */
  isReadOnly: boolean;
  /** True if the record must not be deleted (UI-NFR-018 R-028). */
  isDeletionProtected: boolean;
  /** True if a "copy as template" action should be offered (UI-NFR-018 R-015). */
  canCopyAsTemplate: boolean;
  /** Localised tooltip text for the origin chip / read-only hint. */
  tooltipText: string;
  /** Localised one-line hint to render below the meta row (R-014). */
  readOnlyHint: string;
}

/**
 * UI-NFR-018 §5.2 + R-027/R-028: central read-only logic for origin-tagged
 * entities. Pages call this hook and consume the booleans to hide
 * edit/delete actions consistently.
 */
export function useOriginProtection({ origin, isSystem }: UseOriginProtectionInput): OriginProtection {
  const { t } = useTranslation();

  return useMemo<OriginProtection>(() => {
    const resolved: DataOrigin = origin ?? (isSystem ? 'system' : 'tenant');
    const isReadOnly = resolved === 'system' || resolved === 'enrichment';
    const isDeletionProtected = resolved === 'system';
    const canCopyAsTemplate = resolved === 'system';

    let tooltipKey = 'common.origin.tooltipImport';
    if (resolved === 'system') tooltipKey = 'common.origin.tooltipSystem';
    else if (resolved === 'enrichment') tooltipKey = 'common.origin.tooltipEnrichment';

    return {
      origin: resolved,
      isReadOnly,
      isDeletionProtected,
      canCopyAsTemplate,
      tooltipText: t(tooltipKey),
      readOnlyHint: t('common.origin.readOnlyHint'),
    };
  }, [origin, isSystem, t]);
}
