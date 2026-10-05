import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import type { TenantStatus } from '@/api/types';

const STATUS_COLOR: Record<TenantStatus, ChipProps['color']> = {
  active: 'success',
  suspended: 'default',
  pending_deletion: 'warning',
  orphaned: 'warning',
  deleted: 'error',
};

interface TenantStatusChipProps {
  /** The lifecycle state (#2123); a backend older than #2123 sends only `isActive`. */
  status?: TenantStatus;
  isActive: boolean;
  testId?: string;
}

/**
 * The lifecycle state of a tenant as a chip (REQ-024 AK-64, #2123): active, suspended,
 * deletion scheduled, orphaned (#2134) or being deleted. Falls back to active/suspended
 * from `is_active` when the response carries no `status`.
 */
export default function TenantStatusChip({ status, isActive, testId }: TenantStatusChipProps) {
  const { t } = useTranslation();
  const effective: TenantStatus = status ?? (isActive ? 'active' : 'suspended');
  return (
    <Chip
      label={t(`enums.tenantStatus.${effective}`)}
      color={STATUS_COLOR[effective]}
      size="small"
      data-testid={testId}
    />
  );
}
