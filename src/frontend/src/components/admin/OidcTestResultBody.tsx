import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import type { OidcProviderTestResult } from '@/api/types';

interface Verdict {
  id: string;
  label: string;
  ok: boolean;
  applicable: boolean;
  detail: string;
  extra?: string[];
}

/**
 * The four verdicts of `POST /admin/oidc-providers/{key}/test` plus its discovery message (#1906).
 *
 * Each verdict is a status chip **and** its own words — never colour alone — followed by the
 * server's `detail`, which names the cause (the announced issuer to set, the missing scope).
 */
export default function OidcTestResultBody({ result }: { result: OidcProviderTestResult }) {
  const { t } = useTranslation();
  const verdicts: Verdict[] = [
    {
      id: 'scope',
      label: t('pages.admin.oidc.test.scopeCheck'),
      ok: result.scope_check.ok,
      applicable: true,
      detail: result.scope_check.detail,
    },
    {
      id: 'type',
      label: t('pages.admin.oidc.test.typeCheck'),
      ok: result.provider_type_check.ok,
      applicable: true,
      detail: result.provider_type_check.detail,
    },
    {
      id: 'jwks',
      label: t('pages.admin.oidc.test.jwksCheck'),
      ok: result.jwks_check.ok,
      applicable: result.jwks_check.applicable,
      detail: result.jwks_check.detail,
      extra: result.jwks_check.applicable
        ? [
            t('pages.admin.oidc.test.keys', { count: result.jwks_check.key_count }),
            ...(result.jwks_check.skipped_key_count > 0
              ? [t('pages.admin.oidc.test.skippedKeys', { count: result.jwks_check.skipped_key_count })]
              : []),
          ]
        : undefined,
    },
    {
      id: 'issuer',
      label: t('pages.admin.oidc.test.issuerCheck'),
      ok: result.issuer_check.ok,
      applicable: result.issuer_check.applicable,
      detail: result.issuer_check.detail,
    },
  ];

  return (
    <Box data-testid="oidc-test-result">
      <Typography variant="subtitle2" component="h3" gutterBottom>
        {t('pages.admin.oidc.test.discovery')}
      </Typography>
      <Alert severity="info" sx={{ mb: 2, wordBreak: 'break-word' }} data-testid="oidc-test-message">
        {result.message}
      </Alert>
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {verdicts.map((v) => (
          <Box component="li" key={v.id} data-testid={`oidc-verdict-${v.id}`}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Typography variant="subtitle2" component="h3">
                {v.label}
              </Typography>
              <Chip
                size="small"
                color={!v.applicable ? 'default' : v.ok ? 'success' : 'error'}
                variant={v.applicable ? 'filled' : 'outlined'}
                label={
                  !v.applicable
                    ? t('pages.admin.oidc.test.notApplicable')
                    : v.ok
                      ? t('pages.admin.oidc.test.ok')
                      : t('pages.admin.oidc.test.failed')
                }
                data-testid={`oidc-verdict-${v.id}-status`}
              />
              {v.extra?.map((x) => (
                <Typography key={x} variant="caption" color="text.secondary">
                  {x}
                </Typography>
              ))}
            </Box>
            {v.detail && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, wordBreak: 'break-word' }}>
                {v.detail}
              </Typography>
            )}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
