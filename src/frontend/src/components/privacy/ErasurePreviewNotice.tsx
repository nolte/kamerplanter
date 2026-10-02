import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import type { ErasurePreviewState } from '@/hooks/useErasurePreview';

interface ErasurePreviewNoticeProps {
  preview: ErasurePreviewState;
  /** Prefix of the `data-testid`s, so the page and a dialog can both show it. */
  testIdPrefix: string;
  /** `alert` frames it in a warning `Alert` (the tab panel); `inline` leaves it bare (inside a dialog text). */
  variant?: 'inline' | 'alert';
  /**
   * Whose erasure it is. `self` (default) speaks to the person deleting their own account and
   * promises their members a grace period; `admin` (#1961) is a platform admin deleting another
   * account, which gives the other members none — the text says so.
   */
  audience?: 'self' | 'admin';
}

/**
 * The personal tenants an account erasure deletes with the account, one line
 * each, shown **before** the person confirms (REQ-025 AK-FK-06, #1824).
 *
 * Made of `span`s, not a list: it sits inside `DialogContentText`, which is a
 * `<p>`, where a `<ul>` would be invalid markup. Renders nothing for an account
 * without a personal tenant — and nothing while `idle`, because the caller has
 * not asked yet.
 */
export default function ErasurePreviewNotice({
  preview,
  testIdPrefix,
  variant = 'inline',
  audience = 'self',
}: ErasurePreviewNoticeProps) {
  const { t } = useTranslation();
  const admin = audience === 'admin';
  const block = { display: 'block' } as const;

  let content: ReactNode = null;
  if (preview.status === 'loading') {
    content = (
      <Box
        component="span"
        sx={{ ...block, mt: 1 }}
        role="status"
        data-testid={`${testIdPrefix}-loading`}
      >
        {admin ? t('pages.auth.adminErasurePreviewLoading') : t('pages.privacy.erasurePreviewLoading')}
      </Box>
    );
  } else if (preview.status === 'error') {
    content = (
      <Box
        component="span"
        sx={{ ...block, mt: 1 }}
        role="alert"
        data-testid={`${testIdPrefix}-error`}
      >
        {admin ? t('pages.auth.adminErasurePreviewError') : t('pages.privacy.erasurePreviewError')}
      </Box>
    );
  } else if (preview.status === 'ready' && preview.tenants.length > 0) {
    const anyShared = preview.tenants.some((tenant) => tenant.other_member_count > 0);
    content = (
      <Box component="span" sx={{ ...block, mt: 1 }} data-testid={testIdPrefix}>
        <Box component="strong" sx={block}>
          {admin ? t('pages.auth.adminErasurePreviewHeading') : t('pages.privacy.erasurePreviewHeading')}
        </Box>
        {preview.tenants.map((tenant, index) => (
          // The preview carries no id (names and counts only, AK-FK-06), so the position disambiguates two tenants of one name.
          <Box
            component="span"
            sx={block}
            key={`${tenant.name}-${index}`}
            data-testid={`${testIdPrefix}-tenant`}
          >
            {tenant.other_member_count > 0
              ? admin
                ? t('pages.auth.adminErasurePreviewTenantShared', {
                    name: tenant.name,
                    count: tenant.other_member_count,
                  })
                : t('pages.privacy.erasurePreviewTenantShared', {
                    name: tenant.name,
                    count: tenant.other_member_count,
                  })
              : admin
                ? t('pages.auth.adminErasurePreviewTenantAlone', { name: tenant.name })
                : t('pages.privacy.erasurePreviewTenantAlone', { name: tenant.name })}
          </Box>
        ))}
        {anyShared && (
          <Box
            component="span"
            sx={{ ...block, mt: 1 }}
            data-testid={`${testIdPrefix}-shared-hint`}
          >
            {admin ? t('pages.auth.adminErasurePreviewSharedHint') : t('pages.privacy.erasurePreviewSharedHint')}
          </Box>
        )}
      </Box>
    );
  }

  if (content === null) return null;
  return variant === 'alert' ? (
    <Alert severity="warning" icon={false} sx={{ mb: 2 }}>
      {content}
    </Alert>
  ) : (
    content
  );
}
