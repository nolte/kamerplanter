import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import RepeatIcon from '@mui/icons-material/Repeat';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import OriginChip from '@/components/common/OriginChip';
import PrintButton from '@/components/common/PrintButton';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseEntryDialog from './PhaseEntryDialog';
import DeliveryChannelDialog from './DeliveryChannelDialog';
import ChannelFertilizerDialog from './ChannelFertilizerDialog';
import DosageCalculatorTab from './DosageCalculatorTab';
import WateringLogCreateDialog from '@/pages/giessprotokoll/WateringLogCreateDialog';
import { downloadNutrientPlanPdf } from '@/api/endpoints/print';
import PhaseTimelineTab from './nutrient-plan-detail/PhaseTimelineTab';
import PlanValidationTab from './nutrient-plan-detail/PlanValidationTab';
import PlanEditTab from './nutrient-plan-detail/PlanEditTab';
import { useNutrientPlanDetail } from './nutrient-plan-detail/useNutrientPlanDetail';

export default function NutrientPlanDetailPage() {
  const { t } = useTranslation();
  const c = useNutrientPlanDetail();
  const { key, plan } = c;

  if (c.loading) return <LoadingSkeleton variant="form" />;
  if (c.error) return <ErrorDisplay error={c.error} />;
  if (!plan) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="nutrient-plan-detail-page">
      <UnsavedChangesGuard dirty={c.isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 1,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <PageTitle title={plan.name} sx={{ mb: 0 }} />
          {key && (
            <>
              <Tooltip title={t('pages.nutrientPlans.favToggle')}>
                <IconButton
                  onClick={() => c.toggleFavorite(key)}
                  aria-label={t('pages.nutrientPlans.favToggle')}
                  sx={{ color: c.isFavorite(key) ? 'warning.main' : 'action.disabled' }}
                >
                  {c.isFavorite(key) ? <StarIcon /> : <StarBorderIcon />}
                </IconButton>
              </Tooltip>
              <PrintButton
                onPrint={() => downloadNutrientPlanPdf(key)}
                filename={`nutrient-plan-${key}.pdf`}
                label={t('print.nutrientPlan')}
              />
            </>
          )}
          {plan.is_template && (
            <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />
          )}
          {plan.cycle_restart_from_sequence != null && (
            <Chip
              icon={<RepeatIcon />}
              label={`${t('pages.nutrientPlans.cycleRestartFromSequence')}: #${plan.cycle_restart_from_sequence}`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* UI-NFR-018 R-001: Origin chip in meta row */}
          <OriginChip origin={c.planOrigin} />
          {/* UI-NFR-018 R-015: copy-as-template for system plans.
              AP-12 (FE-L1): the copy endpoint is not implemented yet, so this is an
              honestly disabled button with an explanatory tooltip — never a dummy
              button whose only effect is an info toast (user deception). */}
          {c.canCopyAsTemplate && (
            <Tooltip title={t('common.origin.copyAsTemplateUnavailable')}>
              <span>
                <Button
                  variant="outlined"
                  disabled
                  data-testid="copy-as-template-button"
                >
                  {t('common.origin.copyAsTemplate')}
                </Button>
              </span>
            </Tooltip>
          )}
          {/* UI-NFR-018 R-012: hide delete button for system data */}
          {!c.isDeletionProtected && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => c.setDeleteOpen(true)}
              data-testid="delete-nutrient-plan-button"
            >
              {t('common.delete')}
            </Button>
          )}
        </Box>
      </Box>

      {/* UI-NFR-018 R-014: persistent, origin-specific explanation — visible on
          every tab, so the "why can't I edit this" question is answered before
          the user even opens the Edit tab. */}
      {c.isReadOnly && (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="nutrient-plan-readonly-banner">
          {c.planOriginTooltip}
        </Alert>
      )}

      <Tabs value={c.tab} onChange={(_, v) => c.setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.nutrientPlans.tabPhaseEntries')} {...tabA11yProps('nutrientPlan', 0)} />
        <Tab label={t('pages.nutrientPlans.tabValidation')} {...tabA11yProps('nutrientPlan', 1)} />
        <Tab label={t('pages.nutrientPlans.dosageCalc.tabTitle')} {...tabA11yProps('nutrientPlan', 2)} />
        <Tab label={t('common.edit')} {...tabA11yProps('nutrientPlan', 3)} />
      </Tabs>

      {/* Tab 0: Phase Entries — Timeline-first with Gantt hero */}
      <TabPanel index={0} value={c.tab} idPrefix="nutrientPlan">
        <PhaseTimelineTab
          plan={plan}
          entries={c.entries}
          fertilizers={c.fertilizers}
          expandedEntries={c.expandedEntries}
          toggleExpanded={c.toggleExpanded}
          onAddEntry={c.openAddEntry}
          onEditEntry={c.openEditEntry}
          onDeleteEntry={c.openDeleteEntry}
          onAddChannel={c.openAddChannel}
          onEditChannel={c.onEditChannel}
          onDeleteChannel={c.openDeleteChannel}
          onAddChannelFertilizer={c.onAddChannelFertilizer}
          onEditChannelFertilizer={c.onEditChannelFertilizer}
          onRemoveChannelFertilizer={c.onRemoveChannelFertilizer}
          onRemoveFertilizerFromGantt={c.onRemoveFertilizerFromGantt}
          onEntriesChange={c.handleEntriesChange}
          onLogWatering={c.onLogWatering}
        />
      </TabPanel>

      {/* Tab 1: Validation */}
      <TabPanel index={1} value={c.tab} idPrefix="nutrientPlan">
        <PlanValidationTab
          validation={c.validation}
          validating={c.validating}
          entries={c.entries}
          onEditChannel={c.onEditChannel}
        />
      </TabPanel>

      {/* Tab 2: Dosage Calculator */}
      <TabPanel index={2} value={c.tab} idPrefix="nutrientPlan">
        <DosageCalculatorTab plan={plan} entries={c.entries} />
      </TabPanel>

      {/* Tab 3: Edit */}
      <TabPanel index={3} value={c.tab} idPrefix="nutrientPlan">
        <PlanEditTab
          control={c.control}
          onSubmit={c.handleSubmit(c.onSave)}
          isReadOnly={c.isReadOnly}
          saving={c.saving}
          isDirty={c.isDirty}
          onCancel={c.resetForm}
          scheduleMode={c.editScheduleMode}
          scheduleEnabled={c.editScheduleEnabled}
          weekdaySchedule={c.editWeekdaySchedule}
          onWeekdayToggle={c.handleEditWeekdayToggle}
        />
      </TabPanel>

      {/* Dialogs */}
      <ConfirmDialog
        open={c.deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: plan.name })}
        onConfirm={c.onDelete}
        onCancel={() => c.setDeleteOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={c.deleteEntryOpen}
        title={t('common.delete')}
        message={t('pages.nutrientPlans.deleteEntryConfirm', {
          phase: c.deletingEntry ? t(`enums.phaseName.${c.deletingEntry.phase_name}`) : '',
        })}
        onConfirm={c.onDeleteEntry}
        onCancel={c.cancelDeleteEntry}
        destructive
      />

      <ConfirmDialog
        open={c.deleteChannelOpen}
        title={t('pages.deliveryChannels.deleteChannel')}
        message={t('pages.deliveryChannels.deleteChannelConfirm', {
          label: c.deletingChannelId,
        })}
        onConfirm={c.onDeleteChannel}
        onCancel={c.cancelDeleteChannel}
        destructive
      />

      <ConfirmDialog
        open={c.removeFertAllOpen}
        title={t('common.delete')}
        message={t('pages.fertilizerGantt.removeFertilizerConfirm', {
          name: c.removeFertAllPayload?.fertilizerName ?? '',
        })}
        onConfirm={c.onConfirmRemoveFertilizerFromAll}
        onCancel={c.cancelRemoveFertAll}
        destructive
      />

      {key && (
        <PhaseEntryDialog
          open={c.entryDialogOpen}
          onClose={c.closeEntryDialog}
          planKey={key}
          entry={c.editingEntry}
          onSaved={c.onEntrySaved}
        />
      )}

      <DeliveryChannelDialog
        open={c.channelDialogOpen}
        onClose={c.closeChannelDialog}
        onSave={c.onSaveChannel}
        existingChannel={c.editingChannel}
        existingIds={c.channelDialogExistingIds}
      />

      <ChannelFertilizerDialog
        open={c.fertDialogOpen}
        onClose={c.closeFertDialog}
        onSave={c.onSaveChannelFertilizer}
        fertilizers={c.fertilizers}
        existingFertilizerKeys={c.fertDialogExistingKeys}
        existingDosage={c.editingFertDosage}
      />

      <WateringLogCreateDialog
        open={c.wateringLogOpen}
        onClose={c.closeWateringLog}
        onCreated={c.onWateringLogged}
        channelPreset={c.wateringLogChannel}
        availableFertilizers={c.fertilizers}
      />
    </Box>
  );
}
