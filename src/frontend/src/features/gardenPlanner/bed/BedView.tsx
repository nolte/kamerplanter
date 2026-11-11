/**
 * The bed view (REQ-053 GP-FR-041/047): the bed head from the summary and the tabs Plan, Planting,
 * Care, Soil, History, Photos (GP-FR-051) and Details. The tab is part of the URL hash (`useTabUrl`), so every tab can
 * be linked. "Details" is the location page as it always was (master data, tank, runs, slots,
 * watering, sensors), handed in by `LocationDetailPage`.
 *
 * Offline (REQ-053 WP 9.2) the page hands in the summary from the plan cache with its `cachedAt`: a
 * "Stand von hh:mm" banner says so, and every edit of the bed (status, sun, site conditions, rotation,
 * soil, photos) stays locked with a hint while there is no connection or the summary is the cached one.
 */
import { lazy, Suspense, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import BedHeader from './BedHeader';
import { usePreviousYear } from '../history/usePreviousYear';
import CachedDataBanner from '../offline/CachedDataBanner';
import { useRotationBadge } from '../planting/useRotationBadge';
import BedStatusDialog from './BedStatusDialog';
import RotationSwitch from './RotationSwitch';
import SoilAnalysisSection from './SoilAnalysisSection';
import SoilProfileForm from './SoilProfileForm';
import { allowedBedTransitions } from './bedStatus';
import type { BedSummary } from './types';
import { useBedAssignments } from './useBedAssignments';
import { useLocationTypeNames } from './useLocationTypeNames';
import { useSiteFacts } from './useSiteThresholds';
import { isIndoorPlanSite } from '../model/siteKind';
import { useYearParam } from './useYearParam';

// The renderer is the heavy part; it loads when the Plan tab opens.
const BedPlanTab = lazy(() => import('./BedPlanTab'));
// The care tab brings its dialogs (completion, task, log); they load when the tab opens.
const BedCareTab = lazy(() => import('../care/BedCareTab'));
// The history tab brings the timeline, the filters and the backfill dialog; it loads when the tab opens.
const BedHistoryTab = lazy(() => import('../history/BedHistoryTab'));
// The planting tab brings the planting dialog and the plant actions; they load when the tab opens.
const BedPlantingTab = lazy(() => import('../planting/BedPlantingTab'));
// The photo gallery brings the upload dialog and the viewer; it loads when the tab opens (GP-FR-051).
const BedPhotosTab = lazy(() => import('./BedPhotosTab'));
// The sun tiles load when the dialog opens (GP-FR-157).
const SunDialog = lazy(() => import('./SunDialog'));
// The site conditions (frost, wind, slope, access) load when their dialog opens (GP-FR-162/163/168).
const SiteConditionsDialog = lazy(() => import('./SiteConditionsDialog'));

const ID_PREFIX = 'bed';
const TABS_WITH_PLAN = ['plan', 'planting', 'care', 'soil', 'history', 'photos', 'details'] as const;
const TABS_WITHOUT_PLAN = ['planting', 'care', 'soil', 'history', 'photos', 'details'] as const;

type BedTab = (typeof TABS_WITH_PLAN)[number];

interface BedViewProps {
  summary: BedSummary;
  /** The location page body, shown on the "Details" tab. */
  details: ReactNode;
  /** The summary changed on the server (status, soil); reload it. */
  onReload: () => void | Promise<void>;
  /** The summary comes from the plan cache: epoch milliseconds of the online read; `null`/absent = live. */
  cachedAt?: number | null;
}

export default function BedView({ summary, details, onReload, cachedAt = null }: BedViewProps) {
  const { t } = useTranslation();
  const { canEdit: mayEdit, canDelete } = useTenantPermissions();
  const online = useOnlineStatus();
  // Edits are online-only and never made against a cached state (WP 9.2): locked with a hint, not an error.
  const editsLocked = !online || cachedAt !== null;
  const canEdit = mayEdit && !editsLocked;
  const { isModuleVisible } = useModuleVisibility();
  const planVisible = isModuleVisible('garden_planner');
  const tabIds: readonly BedTab[] = planVisible ? TABS_WITH_PLAN : TABS_WITHOUT_PLAN;
  const [tabIndex, setTabIndex] = useTabUrl(tabIds);
  const typeNames = useLocationTypeNames();
  const assignments = useBedAssignments(true);
  const { year, years, setYear } = useYearParam();
  const [statusOpen, setStatusOpen] = useState(false);
  const [sunOpen, setSunOpen] = useState(false);
  const [siteOpen, setSiteOpen] = useState(false);
  const [plantingVersion, setPlantingVersion] = useState(0);
  const rotationBadge = useRotationBadge(summary.key, plantingVersion);
  // A planting or a filled-in / taken-back year changes what the head says about the previous year (#2764).
  const [historyVersion, setHistoryVersion] = useState(0);
  const previousYear = usePreviousYear(summary.key, year - 1, plantingVersion + historyVersion);
  // The site's sun-class and reach thresholds (GP-FR-164/166, WP 8.24); the defaults until it is read. Its type hides
  // weather, frost and wind on an indoor site (GP-FR-182, WP 10.8).
  const { thresholds, siteType } = useSiteFacts(summary.site_key);

  const targets = useMemo(
    () => (canEdit ? allowedBedTransitions(summary.bed_status, canDelete) : []),
    [canEdit, canDelete, summary.bed_status],
  );
  const assignees = assignments.byLocation.get(summary.key) ?? [];

  const panelFor = (id: BedTab): ReactNode => {
    switch (id) {
      case 'plan':
        return (
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <BedPlanTab bed={summary} planLinkVisible={planVisible} />
          </Suspense>
        );
      case 'planting':
        return (
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <BedPlantingTab
              bed={summary}
              onChanged={() => {
                setPlantingVersion((value) => value + 1);
                void onReload();
              }}
            />
          </Suspense>
        );
      case 'care':
        return (
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <BedCareTab bed={summary} onChanged={() => void onReload()} />
          </Suspense>
        );
      case 'history':
        return (
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <BedHistoryTab
              key={summary.key}
              bed={summary}
              onChanged={() => {
                setHistoryVersion((value) => value + 1);
                void onReload();
              }}
            />
          </Suspense>
        );
      case 'photos':
        return (
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <BedPhotosTab
              key={summary.key}
              bedKey={summary.key}
              bedName={summary.name}
              coverPhotoRef={summary.cover_photo_ref ?? null}
              canEdit={canEdit}
              onCoverChange={() => void onReload()}
            />
          </Suspense>
        );
      case 'soil':
        return (
          <>
            <RotationSwitch
              bedKey={summary.key}
              rotationEnabled={summary.rotation_enabled}
              rotationExempt={summary.rotation_exempt}
              canEdit={canEdit}
              onSaved={onReload}
            />
            <SoilProfileForm
              bedKey={summary.key}
              profile={summary.soil_profile}
              canEdit={canEdit}
              onSaved={() => void onReload()}
            />
            <SoilAnalysisSection
              key={summary.key}
              bedKey={summary.key}
              bedName={summary.name}
              canEdit={canEdit}
              profileVersion={summary.soil_profile}
              onRecorded={() => void onReload()}
            />
          </>
        );
      default:
        return details;
    }
  };

  return (
    <Box data-testid="bed-view" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {cachedAt !== null && <CachedDataBanner cachedAt={cachedAt} testId="bed-view-cached-banner" />}
      {mayEdit && editsLocked && (
        <Alert severity="info" role="status" data-testid="bed-view-edits-locked">
          {t('pages.gardenPlan.offline.bedEditsLocked')}
        </Alert>
      )}
      <BedHeader
        summary={summary}
        typeName={typeNames.get(summary.location_type_key) ?? summary.location_type_key}
        assignees={assignees}
        year={year}
        years={years}
        onYearChange={setYear}
        onChangeStatus={targets.length > 0 ? () => setStatusOpen(true) : null}
        onChangeSun={canEdit ? () => setSunOpen(true) : null}
        onChangeSite={canEdit ? () => setSiteOpen(true) : null}
        outdoorConditions={!isIndoorPlanSite(siteType)}
        rotationReasons={rotationBadge?.reasons}
        reachThresholds={thresholds.reach}
        previousYear={previousYear}
      />

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={tabIndex}
          onChange={(_, value: number) => setTabIndex(value)}
          variant="scrollable"
          scrollButtons="auto"
          aria-label={t('pages.bed.tabs.label')}
          data-testid="bed-tabs"
        >
          {tabIds.map((id, index) => (
            <Tab
              key={id}
              label={t(`pages.bed.tabs.${id}`)}
              {...tabA11yProps(ID_PREFIX, index)}
              data-testid={`bed-tab-${id}`}
              sx={{ minHeight: 48 }}
            />
          ))}
        </Tabs>
      </Box>
      {tabIds.map((id, index) => (
        <TabPanel key={id} index={index} value={tabIndex} idPrefix={ID_PREFIX}>
          {panelFor(id)}
        </TabPanel>
      ))}

      {sunOpen && (
        <Suspense fallback={null}>
          <SunDialog
            bedKey={summary.key}
            bedName={summary.name}
            current={summary.sun_exposure}
            currentProfile={summary.site_conditions?.sun_profile}
            thresholds={thresholds.sun}
            onClose={() => setSunOpen(false)}
            onChanged={() => {
              setSunOpen(false);
              void onReload();
            }}
          />
        </Suspense>
      )}

      {siteOpen && (
        <Suspense fallback={null}>
          <SiteConditionsDialog
            bedKey={summary.key}
            bedName={summary.name}
            current={summary.site_conditions}
            siteType={siteType}
            onClose={() => setSiteOpen(false)}
            onChanged={() => {
              setSiteOpen(false);
              void onReload();
            }}
          />
        </Suspense>
      )}

      {statusOpen && (
        <BedStatusDialog
          open
          bedKey={summary.key}
          current={summary.bed_status}
          targets={targets}
          onClose={() => setStatusOpen(false)}
          onChanged={() => {
            setStatusOpen(false);
            void onReload();
          }}
        />
      )}
    </Box>
  );
}
