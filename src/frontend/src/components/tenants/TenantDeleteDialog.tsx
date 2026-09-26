import { useTranslation } from 'react-i18next';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { toStepUpBody } from '@/utils/stepUp';
import type { TenantDeleteRequest } from '@/api/types';

interface TenantDeleteDialogProps {
  open: boolean;
  tenantName: string;
  tenantSlug: string;
  /** Runs the deletion with the step-up; a rejection is shown inside the dialog. */
  onConfirm: (stepUp: TenantDeleteRequest) => Promise<void>;
  onCancel: () => void;
}

/**
 * Confirms the irreversible erasure of a whole tenant with a step-up (#1791).
 *
 * The backend refuses a tenant deletion unless the body echoes the tenant's slug
 * exactly (422) and, for an account with a local password, carries the current
 * password (401); repeated failures answer 429 `STEP_UP_LOCKED` (#1816). The
 * fail-closed password logic, the in-dialog error and the lockout message live
 * in {@link StepUpConfirmDialog}; this wrapper only maps the slug echo onto the
 * tenant-deletion body and keeps the `tenant-delete-*` test ids.
 */
export default function TenantDeleteDialog({
  open,
  tenantName,
  tenantSlug,
  onConfirm,
  onCancel,
}: TenantDeleteDialogProps) {
  const { t } = useTranslation();

  const handleConfirm = ({ echo, ...credentials }: StepUpConfirmation) =>
    onConfirm({ confirm_slug: echo, ...toStepUpBody(credentials) });

  return (
    <StepUpConfirmDialog
      open={open}
      title={t('pages.auth.tenantDeleteDialogTitle')}
      description={t('pages.auth.adminDeleteTenantConfirm', { name: tenantName })}
      echoLabel={t('pages.auth.tenantDeleteSlugLabel')}
      echoHelper={t('pages.auth.tenantDeleteSlugHelper', { slug: tenantSlug })}
      expectedEcho={tenantSlug}
      echoMatch="exact"
      passwordLabel={t('pages.auth.tenantDeletePasswordLabel')}
      passwordHelper={t('pages.auth.tenantDeletePasswordHelper')}
      confirmLabel={t('pages.auth.adminConfirmDelete')}
      testIdPrefix="tenant-delete"
      stepUpAction="tenant_deletion"
      testIds={{ echo: 'tenant-delete-slug' }}
      onConfirm={handleConfirm}
      onCancel={onCancel}
    />
  );
}
