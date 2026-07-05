import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import SettingsIcon from '@mui/icons-material/Settings';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import type { DataOrigin } from '@/api/types';

/** Origin marker as defined by UI-NFR-018 §3 + §4.2. Canonical type in `@/api/types`. */
export type { DataOrigin };

interface OriginChipProps {
  /** Origin string from REQ-001/REQ-024 entities. Takes precedence over isSystem. */
  origin?: DataOrigin;
  /** Fallback for entities that only carry is_system (no origin field yet). */
  isSystem?: boolean;
  /** Optional test id for E2E selectors. */
  testId?: string;
}

interface VariantConfig {
  labelKey: string;
  tooltipKey: string;
  Icon: typeof SettingsIcon;
  color: 'info' | 'secondary' | 'default';
}

const VARIANTS: Record<Exclude<DataOrigin, 'tenant'>, VariantConfig> = {
  system: {
    labelKey: 'common.origin.system',
    tooltipKey: 'common.origin.tooltipSystem',
    Icon: SettingsIcon,
    color: 'info',
  },
  enrichment: {
    labelKey: 'common.origin.enrichment',
    tooltipKey: 'common.origin.tooltipEnrichment',
    Icon: AutoAwesomeIcon,
    color: 'secondary',
  },
  import: {
    labelKey: 'common.origin.import',
    tooltipKey: 'common.origin.tooltipImport',
    Icon: FileUploadIcon,
    color: 'default',
  },
};

/**
 * UI-NFR-018 R-001..R-010: Origin chip with leading icon, outlined variant
 * and explanatory tooltip. Returns null for tenant data so list cells stay
 * empty for user-owned rows (R-003).
 */
export default function OriginChip({ origin, isSystem, testId }: OriginChipProps) {
  const { t } = useTranslation();

  const resolved: DataOrigin | undefined = origin ?? (isSystem ? 'system' : undefined);
  if (!resolved || resolved === 'tenant') {
    return null;
  }

  const variant = VARIANTS[resolved];
  const Icon = variant.Icon;

  return (
    <Tooltip title={t(variant.tooltipKey)} arrow>
      <Chip
        icon={<Icon fontSize="small" />}
        label={t(variant.labelKey)}
        color={variant.color}
        size="small"
        variant="outlined"
        data-testid={testId ?? `origin-chip-${resolved}`}
      />
    </Tooltip>
  );
}
