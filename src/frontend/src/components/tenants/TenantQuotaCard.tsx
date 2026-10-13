import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import EntitlementUsageList from '@/components/tenants/EntitlementUsageList';
import { useTenantEntitlements } from '@/hooks/useTenantEntitlements';

interface TenantQuotaCardProps {
  /** The active garden. */
  slug: string;
  /** Whether the reader is a `lead` here — only the explanation differs; the backend decides what is listed. */
  isLead: boolean;
}

/**
 * The card "Quotas" in the garden settings (REQ-056 §7.7, §15, AK-45).
 *
 * Shown to every member: reading is open to all of them (REQ-024 §1a). The backend already leaves
 * out what a member who is not a lead may not see (service accounts, AI tokens) and counts the
 * per-account AI budget for the reader only, so the card renders the answer as it comes and only
 * says out loud why a member sees fewer rows than a lead. The plan itself is chosen by the operator
 * of the installation — the card says so instead of offering a control that does not exist.
 */
export default function TenantQuotaCard({ slug, isLead }: TenantQuotaCardProps) {
  const { t } = useTranslation();
  const { entitlements, status, reload } = useTenantEntitlements(slug);

  return (
    <Card sx={{ mb: 3 }} data-testid="tenant-quota-card">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 1 }}>
          <DataUsageIcon color="primary" aria-hidden />
          <Typography variant="h6" component="h2">
            {t('pages.tenants.quota.title')}
          </Typography>
          {entitlements && (
            <Chip
              size="small"
              variant="outlined"
              color="primary"
              label={t('pages.tenants.quota.planChip', { name: entitlements.plan.name })}
              data-testid="tenant-quota-plan"
            />
          )}
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {isLead ? t('pages.tenants.quota.introLead') : t('pages.tenants.quota.introMember')}
        </Typography>

        {status === 'loading' && (
          <Box aria-busy="true" data-testid="tenant-quota-loading">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} variant="rounded" height={32} sx={{ mb: 1 }} />
            ))}
          </Box>
        )}
        {status === 'error' && (
          <Alert
            severity="warning"
            data-testid="tenant-quota-error"
            action={
              <Button color="inherit" size="small" onClick={reload} data-testid="tenant-quota-retry">
                {t('common.retry')}
              </Button>
            }
          >
            {t('pages.tenants.quota.loadFailed')}
          </Alert>
        )}
        {status === 'ready' && entitlements && (
          <>
            <EntitlementUsageList limits={entitlements.limits} perspective="member" testIdPrefix="tenant-quota" />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
              {t('pages.tenants.quota.footnote')}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}
