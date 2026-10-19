/**
 * Field mode of the garden plan (REQ-053 §18, GP-UX-020…025/029/030): the phone in the garden, wet hands,
 * sun on the display. It starts with "My beds · due today" - the list loads first, the plan geometry
 * after it (two requests, GP-UX-030) - and offers "Map" as the second tab. A tap on a bed opens its sheet.
 *
 * The whole view uses the high-contrast kiosk theme: text ≥ 7:1 and touch targets of 64 px
 * (`KIOSK_TOUCH_TARGET`, GP-UX-020/021). There are no drawing tools, no grid, no handles and no
 * destructive actions (GP-UX-023); import and export stay in planning mode. Tenant, site, tab and the map
 * view are remembered per device (localStorage).
 *
 * This module is its own lazy chunk: the planning route loads it only in field mode, so it does not
 * count against the garden-planner route budget.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';
import { ThemeProvider } from '@mui/material/styles';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DesignServicesIcon from '@mui/icons-material/DesignServices';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import { kioskHighContrastTheme } from '@/theme/theme';
import type { BedListItem } from '../bed/types';
import { useBedAssignments } from '../bed/useBedAssignments';
import type { PlanRenderer, RendererLabels } from '../renderer/types';
import { loadGardenPlan, resetGardenPlan, selectGardenPlanState } from '../state/gardenPlanSlice';
import FieldBedList from './FieldBedList';
import FieldBedSheet from './FieldBedSheet';
import FieldMap from './FieldMap';
import { sortFieldBeds, todayUtc } from './fieldDue';
import {
  readFieldPrefs,
  rememberFieldSite,
  rememberFieldViewport,
  type FieldTab,
  type FieldViewport,
} from './fieldPrefs';
import { useFieldBeds } from './useFieldBeds';
import { useOnlineStatus } from './useOnlineStatus';

interface FieldModeViewProps {
  siteKey: string;
  /** The renderer the route chose (GP-NFR-009); field mode only draws and hit-tests with it. */
  renderer: PlanRenderer;
  labels: RendererLabels;
  /** Where "Planning mode" leads: the same plan without `?mode=field`. */
  planningHref: string;
}

export default function FieldModeView({ siteKey, renderer, labels, planningHref }: FieldModeViewProps) {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const online = useOnlineStatus();
  const userKey = useAppSelector((state) => state.auth.user?.key ?? null);
  const tenantSlug = useAppSelector((state) => state.tenants.activeTenant?.slug ?? null);
  const { plan, loadStatus, loadError } = useAppSelector(selectGardenPlanState);
  const beds = useFieldBeds(siteKey);
  const assignments = useBedAssignments(true);
  const [prefs] = useState(() => readFieldPrefs(userKey));
  const samePlace = prefs !== null && prefs.tenantSlug === tenantSlug && prefs.siteKey === siteKey;
  const [tab, setTab] = useState<FieldTab>(samePlace ? prefs.tab : 'list');
  // The view last stored for this site. The map is mounted afresh on every tab switch, so it starts from
  // this state - not from the record read at mount, which would bring back a view the user already left.
  const [lastView, setLastView] = useState<{ siteKey: string; view: FieldViewport } | null>(() => {
    const view = samePlace ? prefs.viewports[siteKey] : undefined;
    return view ? { siteKey, view } : null;
  });
  const [openBedKey, setOpenBedKey] = useState<string | null>(null);

  // GP-UX-030: the list first, then the geometry. The plan is forgotten when field mode is left.
  const { settled } = beds;
  useEffect(() => {
    if (settled) void dispatch(loadGardenPlan(siteKey));
  }, [settled, dispatch, siteKey]);
  useEffect(
    () => () => {
      dispatch(resetGardenPlan());
    },
    [dispatch, siteKey],
  );

  const context = useMemo(
    () => (userKey && tenantSlug ? { userKey, tenantSlug, siteKey } : null),
    [userKey, tenantSlug, siteKey],
  );
  useEffect(() => {
    if (context) rememberFieldSite({ ...context, tab });
  }, [context, tab]);
  const onViewChange = useCallback(
    (view: FieldViewport) => {
      setLastView({ siteKey, view });
      if (context) rememberFieldViewport(context, view);
    },
    [context, siteKey],
  );
  const initialView = lastView?.siteKey === siteKey ? lastView.view : null;

  // Planting and a position correction change what the map draws: reload the plan (geometry, plants)
  // with the same thunk that loaded it. The map stays on screen meanwhile (see the map panel below).
  const reloadPlan = useCallback(() => {
    void dispatch(loadGardenPlan(siteKey));
  }, [dispatch, siteKey]);

  const siteName = plan?.siteKey === siteKey ? plan.siteName : null;
  useEffect(() => {
    if (siteName === null) return undefined;
    dispatch(
      setBreadcrumbs([
        { label: 'nav.dashboard', path: '/dashboard' },
        { label: 'nav.sites', path: '/standorte/sites' },
        { label: siteName, path: `/standorte/sites/${siteKey}` },
        { label: 'nav.gardenPlan' },
      ]),
    );
    return () => {
      dispatch(setBreadcrumbs([]));
    };
  }, [dispatch, siteKey, siteName]);

  const today = todayUtc();
  // "My beds" come first, so the list waits for the assignments: sorted before they arrive it would
  // reorder under the user's finger once they do. Without a tenant there is nothing to wait for.
  const assignmentsSettled = assignments.ready || tenantSlug === null;
  const list = beds.state.status === 'ready' && assignmentsSettled ? beds.state.beds : null;
  const listLoading = beds.state.status === 'loading' || (beds.state.status === 'ready' && !assignmentsSettled);
  const sorted = useMemo(
    () => (list ? sortFieldBeds(list, assignments.mine, today, i18n.language) : []),
    [list, assignments.mine, today, i18n.language],
  );
  const bedKeys = useMemo(() => new Set(sorted.map((bed) => bed.key)), [sorted]);
  const openBed: BedListItem | null = sorted.find((bed) => bed.key === openBedKey) ?? null;
  const { reload } = beds;

  const tabButtonSx = { minHeight: KIOSK_TOUCH_TARGET, fontSize: '1rem', textTransform: 'none' } as const;

  return (
    <ThemeProvider theme={kioskHighContrastTheme}>
      <Box
        data-testid="garden-plan-field-mode"
        sx={{
          bgcolor: 'background.paper',
          color: 'text.primary',
          p: { xs: 1, sm: 2 },
          borderRadius: 1,
          fontSize: '1rem',
          '& .MuiTypography-body2': { fontSize: '1rem' },
        }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h4" component="h1" sx={{ flex: '1 1 12rem', overflowWrap: 'anywhere' }}>
            {siteName ?? t('pages.gardenPlan.field.title')}
          </Typography>
          <Button
            component={RouterLink}
            to={`/standorte/sites/${siteKey}`}
            variant="outlined"
            color="inherit"
            startIcon={<ArrowBackIcon />}
            sx={{ minHeight: KIOSK_TOUCH_TARGET, borderWidth: 2 }}
            data-testid="garden-plan-back-link"
          >
            {t('pages.gardenPlan.backToSite')}
          </Button>
          <Button
            component={RouterLink}
            to={planningHref}
            variant="outlined"
            color="inherit"
            startIcon={<DesignServicesIcon />}
            sx={{ minHeight: KIOSK_TOUCH_TARGET, borderWidth: 2 }}
            data-testid="garden-plan-mode-planning"
          >
            {t('pages.gardenPlan.field.toPlanning')}
          </Button>
        </Box>

        {!online && (
          <Alert severity="warning" sx={{ mb: 2 }} data-testid="field-offline">
            {t('pages.gardenPlan.field.offline')}
          </Alert>
        )}

        <Tabs
          value={tab}
          onChange={(_, value: FieldTab) => setTab(value)}
          variant="fullWidth"
          aria-label={t('pages.gardenPlan.field.tabs.label')}
          sx={{ mb: 2, borderBottom: 2, borderColor: 'divider' }}
        >
          <Tab
            value="list"
            label={t('pages.gardenPlan.field.tabs.list')}
            id="field-tab-list"
            aria-controls="field-panel-list"
            sx={tabButtonSx}
            data-testid="field-tab-list"
          />
          <Tab
            value="map"
            label={t('pages.gardenPlan.field.tabs.map')}
            id="field-tab-map"
            aria-controls="field-panel-map"
            sx={tabButtonSx}
            data-testid="field-tab-map"
          />
        </Tabs>

        <Box role="tabpanel" id="field-panel-list" aria-labelledby="field-tab-list" hidden={tab !== 'list'}>
          {tab === 'list' && (
            <>
              {listLoading && (
                <Box role="status" aria-busy="true" aria-label={t('pages.gardenPlan.field.list.loading')}>
                  <LoadingSkeleton variant="card" />
                </Box>
              )}
              {beds.state.status === 'error' && <ErrorDisplay error={beds.state.message} onRetry={reload} />}
              {list && beds.reloadError && (
                <Alert
                  severity="warning"
                  sx={{ mb: 2 }}
                  data-testid="field-list-reload-failed"
                  action={
                    <Button
                      color="inherit"
                      onClick={reload}
                      sx={{ minHeight: KIOSK_TOUCH_TARGET }}
                      data-testid="field-list-reload-retry"
                    >
                      {t('common.retry')}
                    </Button>
                  }
                >
                  {t('pages.gardenPlan.field.list.reloadFailed')}
                </Alert>
              )}
              {list && (
                <FieldBedList
                  beds={sorted}
                  mine={assignments.mine}
                  today={today}
                  onOpen={(bed) => setOpenBedKey(bed.key)}
                />
              )}
            </>
          )}
        </Box>

        <Box role="tabpanel" id="field-panel-map" aria-labelledby="field-tab-map" hidden={tab !== 'map'}>
          {tab === 'map' && (
            <>
              {loadStatus === 'error' && loadError && (
                <ErrorDisplay error={loadError} onRetry={() => void dispatch(loadGardenPlan(siteKey))} />
              )}
              {loadStatus !== 'error' && plan === null && (
                <Box role="status" aria-busy="true" aria-label={t('pages.gardenPlan.field.map.loading')}>
                  <LoadingSkeleton variant="card" />
                </Box>
              )}
              {/* A reload after planting keeps the drawn plan (and the map's view) until the new one is in. */}
              {plan !== null && loadStatus !== 'error' && (
                <FieldMap
                  plan={plan}
                  renderer={renderer}
                  labels={labels}
                  bedKeys={bedKeys}
                  selectedBedKey={openBedKey}
                  initialView={initialView}
                  onViewChange={onViewChange}
                  onSelectBed={setOpenBedKey}
                />
              )}
            </>
          )}
        </Box>

        {openBed && (
          <FieldBedSheet
            key={openBed.key}
            bed={openBed}
            online={online}
            onClose={() => setOpenBedKey(null)}
            onChanged={reload}
            onPlanChanged={reloadPlan}
          />
        )}
      </Box>
    </ThemeProvider>
  );
}
