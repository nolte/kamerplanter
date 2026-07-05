import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Checkbox from '@mui/material/Checkbox';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSeasonOverview } from '@/store/slices/seasonSlice';
import * as overwinteringApi from '@/api/endpoints/overwinteringProfiles';
import type { OverwinteringProfile, SpringAction } from '@/api/types';

/** The staggered hardening-off checklist steps (REQ-047 §4.2). */
const HARDEN_OFF_STEPS = ['step1', 'step2', 'step3'] as const;

/**
 * Earliest upcoming forecast frost date across the given ISO date strings, or
 * `null` if none lie in the future. Kept as a module-level helper so the
 * `Date.now()` read stays out of the component/hook body (React purity rule).
 */
function earliestUpcomingFrost(isoDates: (string | null)[]): Date | null {
  const now = Date.now();
  const times = isoDates
    .filter((d): d is string => Boolean(d))
    .map((d) => new Date(d).getTime())
    .filter((ts) => !Number.isNaN(ts) && ts >= now);
  if (times.length === 0) return null;
  return new Date(Math.min(...times));
}

/**
 * REQ-047 §4.2 — spring return assistant.
 *
 * Appears on the care dashboard only while at least one outdoor/greenhouse site
 * is in the `pre_spring` phase. Guides the user through the staggered hardening
 * ("Abhärten") process, lists the per-plant spring actions (uncover, pre-sprout,
 * move outdoors …) derived from the auto-materialised overwintering profiles,
 * and warns — with live weather data — before putting plants out too early.
 */
export default function SpringReturnAssistant() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const overview = useAppSelector((s) => s.season.overview);
  const [profiles, setProfiles] = useState<OverwinteringProfile[]>([]);
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  useEffect(() => {
    dispatch(fetchSeasonOverview());
  }, [dispatch]);

  const preSpringSites = useMemo(
    () => overview.filter((s) => s.phase === 'pre_spring'),
    [overview],
  );

  const isPreSpring = preSpringSites.length > 0;

  useEffect(() => {
    if (!isPreSpring) return;
    let ignore = false;
    overwinteringApi
      .listOverwinteringProfiles(0, 200)
      .then((list) => {
        if (!ignore) setProfiles(list);
      })
      .catch(() => {
        if (!ignore) setProfiles([]);
      });
    return () => {
      ignore = true;
    };
  }, [isPreSpring]);

  const locale = i18n.language === 'de' ? 'de-DE' : 'en-GB';

  // Earliest upcoming forecast frost across the pre-spring sites (live tier).
  const lateFrostDate = useMemo(
    () =>
      earliestUpcomingFrost(
        preSpringSites.map((s) => s.forecast_first_frost_date),
      ),
    [preSpringSites],
  );

  // Spring actions grouped by the concrete SpringAction so the checklist reads
  // as "these plants need uncovering / pre-sprouting / moving outdoors".
  const springGroups = useMemo(() => {
    const groups = new Map<SpringAction, OverwinteringProfile[]>();
    for (const p of profiles) {
      if (!p.spring_action) continue;
      const existing = groups.get(p.spring_action) ?? [];
      existing.push(p);
      groups.set(p.spring_action, existing);
    }
    return [...groups.entries()];
  }, [profiles]);

  if (!isPreSpring) return null;

  return (
    <Card sx={{ mb: 3 }} data-testid="spring-return-assistant">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <LocalFloristIcon color="primary" />
          <Typography variant="h6" component="h2">
            {t('pages.season.spring.title')}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.season.spring.subtitle')}
        </Typography>

        {lateFrostDate && (
          <Alert
            severity="warning"
            icon={<WbSunnyIcon />}
            sx={{ mb: 2 }}
            data-testid="spring-late-frost-warning"
          >
            {t('pages.season.spring.lateFrostWarning', {
              date: lateFrostDate.toLocaleDateString(locale, {
                day: '2-digit',
                month: 'long',
              }),
            })}
          </Alert>
        )}

        {/* Staggered hardening-off checklist (Abhärten). */}
        <Tooltip title={t('pages.season.spring.hardenOffHelp')} arrow enterTouchDelay={0}>
          <Typography
            variant="subtitle2"
            sx={{ cursor: 'help', textDecoration: 'underline dotted' }}
          >
            {t('pages.season.spring.hardenOffTitle')}
          </Typography>
        </Tooltip>
        <List dense data-testid="spring-harden-off-list">
          {HARDEN_OFF_STEPS.map((step) => {
            const id = `harden-${step}`;
            return (
              <ListItem key={step} disableGutters sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <Checkbox
                    edge="start"
                    size="small"
                    checked={checked[id] ?? false}
                    onChange={(e) =>
                      setChecked((prev) => ({ ...prev, [id]: e.target.checked }))
                    }
                    slotProps={{
                      input: {
                        'aria-label': t(`pages.season.spring.hardenOff.${step}`),
                      },
                    }}
                  />
                </ListItemIcon>
                <ListItemText primary={t(`pages.season.spring.hardenOff.${step}`)} />
              </ListItem>
            );
          })}
        </List>

        {springGroups.length > 0 && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.season.spring.actionsTitle')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {springGroups.map(([action, entries]) => (
                <Box key={action} data-testid={`spring-action-${action}`}>
                  <Chip
                    label={t(`enums.springAction.${action}`)}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mb: 0.5 }}
                  />
                  <List dense disablePadding>
                    {entries.map((p) => (
                      <ListItem key={p.key} disableGutters sx={{ py: 0 }}>
                        <ListItemText
                          primary={
                            p.plant_key ??
                            p.planting_run_key ??
                            t('pages.dashboard.winterProtection.unknownSubject')
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
}
