import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import type { EntitlementUsage } from '@/api/types';
import { formatUsage, usageColor, usagePercent } from '@/utils/entitlements';

interface EntitlementUsageListProps {
  limits: readonly EntitlementUsage[];
  /**
   * Whose view this is. `member`: the garden settings, where the per-account AI counter is the
   * reader's own ("your AI questions today"). `admin`: the platform admin's tenant page, where that
   * counter is the admin's own count in the tenant — normally 0 — and is labelled so.
   */
  perspective: 'member' | 'admin';
  /** Prefix of the per-row test ids. */
  testIdPrefix: string;
}

/**
 * Limit and usage per quota dimension as a list with a progress bar (REQ-056 §7.7, §15).
 *
 * A list rather than a table so it reads the same on a phone (§15: "on the smartphone as a list").
 * A bar is drawn only where there is something to measure — an unlimited dimension, or one counted
 * per plant, says so in words instead of showing an empty bar that would read as "nothing used".
 */
export default function EntitlementUsageList({ limits, perspective, testIdPrefix }: EntitlementUsageListProps) {
  const { t } = useTranslation();

  return (
    <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
      {limits.map((row) => {
        const percent = usagePercent(row);
        const labelId = `${testIdPrefix}-${row.dimension}-label`;
        const label =
          row.dimension === 'ai_calls_per_user_day'
            ? t(`pages.plans.usage.ownAiCalls.${perspective}`)
            : t(`enums.entitlementDimension.${row.dimension}`);
        const usageText = formatUsage(row, t);
        return (
          <Box component="li" key={row.dimension} data-testid={`${testIdPrefix}-${row.dimension}`}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                alignItems: { sm: 'baseline' },
                gap: { xs: 0.25, sm: 2 },
                mb: 0.5,
              }}
            >
              <Typography id={labelId} variant="body2" sx={{ fontWeight: 500 }}>
                {label}
              </Typography>
              <Typography
                variant="body2"
                color={percent !== null && percent >= 100 ? 'error' : 'text.secondary'}
                data-testid={`${testIdPrefix}-${row.dimension}-value`}
              >
                {usageText}
              </Typography>
            </Box>
            {percent !== null && (
              <LinearProgress
                variant="determinate"
                value={percent}
                color={usageColor(percent)}
                aria-labelledby={labelId}
                aria-valuetext={usageText}
                sx={{ height: 8, borderRadius: 1 }}
                data-testid={`${testIdPrefix}-${row.dimension}-bar`}
              />
            )}
          </Box>
        );
      })}
    </Box>
  );
}
