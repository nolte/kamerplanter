/**
 * The bed view (REQ-053 GP-FR-041/047): the bed head from the summary and the tabs Plan, Planting,
 * Care, Soil, History and Details. The tab is part of the URL hash (`useTabUrl`), so every tab can
 * be linked. "Details" is the location page as it always was (master data, tank, runs, slots,
 * watering, sensors), handed in by `LocationDetailPage`.
 */
import { lazy, Suspense, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import BedHeader from './BedHeader';
import BedPlaceholderPanel from './BedPlaceholderPanel';
import { useRotationBadge } from '../planting/useRotationBadge';
import BedStatusDialog from './BedStatusDialog';
import SoilProfileForm from './SoilProfileForm';
import { allowedBedTransitions } from './bedStatus';
import type { BedSummary } from './types';
import { useBedAssignments } from './useBedAssignments';
import { useLocationTypeNames } from './useLocationTypeNames';
import { useYearParam } from './useYearParam';

// The renderer is the heavy part; it loads when the Plan tab opens.
const BedPlanTab = lazy(() => import('./BedPlanTab'));
// The care tab brings its dialogs (completion, task, log); they load when the tab opens.
const BedCareTab = lazy(() => import('../care/BedCareTab'));
// The planting tab brings the planting dialog and the plant actions; they load when the tab opens.
const BedPlantingTab = lazy(() => import('../planting/BedPlantingTab'));

const ID_PREFIX = 'bed';
const TABS_WITH_PLAN = ['plan', 'planting', 'care', 'soil', 'history', 'details'] as const;
const TABS_WITHOUT_PLAN = ['planting', 'care', 'soil', 'history', 'details'] as const;

type BedTab = (typeof TABS_WITH_PLAN)[number];

interface BedViewProps {
  summary: BedSummary;
  /** The location page body, shown on the "Details" tab. */
  details: ReactNode;
  /** The summary changed on the server (status, soil); reload it. */
  onReload: () => void | Promise<void>;
}

export default function BedView({ summary, details, onReload }: BedViewProps) {
  const { t } = useTranslation();
  const { canEdit, canDelete } = useTenantPermissions();
  const { isModuleVisible } = useModuleVisibility();
  const planVisible = isModuleVisible('garden_planner');
  const tabIds: readonly BedTab[] = planVisible ? TABS_WITH_PLAN : TABS_WITHOUT_PLAN;
  const [tabIndex, setTabIndex] = useTabUrl(tabIds);
  const typeNames = useLocationTypeNames();
  const assignments = useBedAssignments(true);
  const { year, years, setYear } = useYearParam();
  const [statusOpen, setStatusOpen] = useState(false);
  const [plantingVersion, setPlantingVersion] = useState(0);
  const rotationBadge = useRotationBadge(summary.key, plantingVersion);

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
        return <BedPlaceholderPanel tab="history" />;
      case 'soil':
        return (
          <SoilProfileForm
            bedKey={summary.key}
            profile={summary.soil_profile}
            canEdit={canEdit}
            onSaved={() => void onReload()}
          />
        );
      default:
        return details;
    }
  };

  return (
    <Box data-testid="bed-view" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <BedHeader
        summary={summary}
        typeName={typeNames.get(summary.location_type_key) ?? summary.location_type_key}
        assignees={assignees}
        year={year}
        years={years}
        onYearChange={setYear}
        onChangeStatus={targets.length > 0 ? () => setStatusOpen(true) : null}
        rotationReasons={rotationBadge?.reasons}
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
