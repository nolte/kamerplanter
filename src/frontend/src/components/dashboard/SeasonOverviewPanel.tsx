import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider';
import type { SvgIconComponent } from '@mui/icons-material';
import EnergySavingsLeafIcon from '@mui/icons-material/EnergySavingsLeaf';
import SevereColdIcon from '@mui/icons-material/SevereCold';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import SensorsIcon from '@mui/icons-material/Sensors';
import PublicIcon from '@mui/icons-material/Public';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSeasonOverview } from '@/store/slices/seasonSlice';
import { fetchSites } from '@/store/slices/sitesSlice';
import type { SeasonPhase, SeasonTriggerTier } from '@/api/types';

/**
 * REQ-047 §4.1 — icon per season phase so the state is never colour-only
 * (WCAG 1.4.1): a leaf (growing), a cold warning (pre_winter), a snowflake
 * (winter dormancy) and a bud (spring reactivation).
 */
const phaseIcon: Record<SeasonPhase, SvgIconComponent> = {
  growing: EnergySavingsLeafIcon,
  pre_winter: SevereColdIcon,
  winter_dormancy: AcUnitIcon,
  pre_spring: LocalFloristIcon,
};

const phaseColor: Record<
  SeasonPhase,
  'success' | 'warning' | 'info' | 'primary'
> = {
  growing: 'success',
  pre_winter: 'warning',
  winter_dormancy: 'info',
  pre_spring: 'primary',
};

const triggerIcon: Record<SeasonTriggerTier, SvgIconComponent> = {
  live: SensorsIcon,
  climatological: PublicIcon,
  calendar: CalendarMonthIcon,
};

/** Days from today (calendar days) until an ISO date, or null if unparseable. */
function daysUntil(isoDate: string): number | null {
  const target = new Date(isoDate);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const t1 = new Date(
    target.getFullYear(),
    target.getMonth(),
    target.getDate(),
  );
  return Math.round((t1.getTime() - t0.getTime()) / 86_400_000);
}

/**
 * REQ-047 §4.1 — per-outdoor-site season status. Rendered inside the existing
 * REQ-022 winter-protection widget. Shows the current season phase, the trigger
 * source (live weather / climate estimate / calendar) as a badge, and a frost
 * countdown so the user can tell whether a warning rests on real data.
 *
 * Self-fetches the season overview and the site list (to resolve site names).
 */
export default function SeasonOverviewPanel() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const { overview, overviewLoading, overviewError } = useAppSelector(
    (s) => s.season,
  );
  const sites = useAppSelector((s) => s.sites.sites);

  useEffect(() => {
    dispatch(fetchSeasonOverview());
    dispatch(fetchSites({ limit: 200 }));
  }, [dispatch]);

  const siteNameByKey = useMemo(() => {
    const map = new Map<string, string>();
    for (const site of sites) map.set(site.key, site.name);
    return map;
  }, [sites]);

  const locale = i18n.language === 'de' ? 'de-DE' : 'en-GB';

  const formatMonthDay = useMemo(
    () => (md: string): string => {
      const [month, day] = md.split('-').map((n) => Number.parseInt(n, 10));
      if (!month || !day) return md;
      // Reference year is irrelevant — only day + month are shown.
      return new Date(2024, month - 1, day).toLocaleDateString(locale, {
        day: '2-digit',
        month: 'long',
      });
    },
    [locale],
  );

  // Nothing to show at all: hide the whole panel (the traffic light below still
  // renders) rather than showing an empty header. Errors degrade silently — the
  // season panel is auxiliary to the winter-hardiness overview.
  if (
    (!overview || overview.length === 0) &&
    !overviewLoading &&
    !overviewError
  ) {
    return null;
  }

  if (overviewError) return null;

  if (overview.length === 0) return null;

  return (
    <Box data-testid="season-overview-panel" sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('pages.season.overviewTitle')}
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {overview.map((state) => {
          const PhaseIcon = phaseIcon[state.phase];
          const TriggerIcon = triggerIcon[state.trigger_tier];
          const color = phaseColor[state.phase];
          const siteName =
            siteNameByKey.get(state.site_key) ?? state.site_key;

          // Frost countdown: prefer the live forecast date, fall back to the
          // climatological "typical first frost" month/day.
          let frostLabel: string | null = null;
          if (state.forecast_first_frost_date) {
            const days = daysUntil(state.forecast_first_frost_date);
            if (days != null) {
              frostLabel =
                days <= 0
                  ? t('pages.season.frost.now')
                  : t('pages.season.frost.inDays', { count: days });
            }
          } else if (state.estimated_first_frost_md) {
            frostLabel = t('pages.season.frost.typical', {
              date: formatMonthDay(state.estimated_first_frost_md),
            });
          }

          return (
            <Box
              key={state.site_key}
              data-testid={`season-row-${state.site_key}`}
              sx={{
                // Mobile-first: stack the label/phase and the badges vertically
                // on phones, spread them onto one row from sm upwards.
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                alignItems: { xs: 'flex-start', sm: 'center' },
                justifyContent: 'space-between',
                gap: 1,
                px: 1.5,
                py: 1,
                borderRadius: 1,
                border: 1,
                borderColor: 'divider',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                <Tooltip title={t(`pages.season.phaseHelp.${state.phase}`)} arrow enterTouchDelay={0}>
                  <PhaseIcon
                    fontSize="small"
                    sx={{ color: `${color}.main` }}
                    aria-hidden="true"
                  />
                </Tooltip>
                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
                    {siteName}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {t(`enums.seasonPhase.${state.phase}`)}
                  </Typography>
                  {/* Natural-language reason from the backend (e.g. frost forecast). */}
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {t(state.trigger_reason_i18n_key, {
                      defaultValue: t('pages.season.trigger.unknown'),
                    })}
                  </Typography>
                </Box>
              </Box>

              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                  flexWrap: 'wrap',
                }}
              >
                {frostLabel && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    data-testid={`season-frost-${state.site_key}`}
                  >
                    {frostLabel}
                  </Typography>
                )}
                <Tooltip
                  title={t(`pages.season.triggerHelp.${state.trigger_tier}`)}
                  arrow
                  enterTouchDelay={0}
                >
                  <Chip
                    icon={<TriggerIcon />}
                    label={t(`enums.seasonTriggerTier.${state.trigger_tier}`)}
                    size="small"
                    variant="outlined"
                    color={state.trigger_tier === 'live' ? 'info' : 'default'}
                    data-testid={`season-trigger-${state.site_key}`}
                  />
                </Tooltip>
              </Box>
            </Box>
          );
        })}
      </Box>
      <Divider sx={{ mt: 2 }} />
    </Box>
  );
}
