/**
 * The bed sheet of field mode (REQ-053 §18.1 steps 3-9, GP-UX-023/025/029, GP-FR-149): a bottom sheet
 * with the bed's name, the quick protocol, the tasks (overdue first) and the plants. Everything appears
 * on a tap - there is no hover in the field (GP-UX-025) - and every action is sent at once, there is no
 * dirty state (GP-UX-003, F-16).
 *
 * "Done" → short dialog → "Finish" is two taps after the bed was chosen (GP-ACC-029). A second tap within
 * 300 ms, or while the first is waiting for its answer, is the same tap; while offline "Done" is locked
 * instead of losing the entry (no offline buffer before wave 9, D-23). Every write offers "Undo" for 8 s.
 */
import { lazy, Suspense, useCallback, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import type { BedListItem } from '../bed/types';
import { completeBedTask, logCareEvent, reopenWithUndo, voidCareEvent } from '../care/careApi';
import type { CareContext } from '../care/careCategories';
import { careCategoryLabel, careTaskName } from '../care/careLabels';
import CareCompletionDialog from '../care/CareCompletionDialog';
import type { CareEventRef, CareTask, CompletionPayload } from '../care/careTypes';
import { isDuplicateTap } from '../care/submitGuard';
import { useUndoSnackbar } from '../care/useUndoSnackbar';
import type { PlantStateWire } from '../planting/plantStateApi';
import { fieldTaskSections, todayUtc } from './fieldDue';
import { groupPlants } from './fieldPlants';
import FieldPlantSection from './FieldPlantSection';
import FieldTaskSection from './FieldTaskSection';
import QuickProtocolChips from './QuickProtocolChips';
import { quickLogBody, type QuickChip } from './quickChips';
import { useBedSheet } from './useBedSheet';

const CareLogDialog = lazy(() => import('../care/CareLogDialog'));
const PlantingDialog = lazy(() => import('../planting/PlantingDialog'));
const PositionCorrectionDialog = lazy(() => import('../planting/PositionCorrectionDialog'));
const PlantPhotoUploadDialog = lazy(() => import('@/pages/pflanzen/photos/PlantPhotoUploadDialog'));

/** Field mode moves a plant by 10 cm per step (§18.1 step 9, F-16). */
export const FIELD_STEP_CM = 10;
/** Long press before a marker can be dragged (GP-UX-023). */
export const FIELD_LONG_PRESS_MS = 500;

interface FieldBedSheetProps {
  bed: BedListItem;
  online: boolean;
  onClose: () => void;
  /** Something the bed list counts changed (tasks, plants); the list reloads. */
  onChanged: () => void;
  /** Something the map draws changed (plants planted or moved); the plan reloads. */
  onPlanChanged: () => void;
}

type Overlay =
  | { kind: 'complete'; task: CareTask }
  | { kind: 'form'; category: string }
  | { kind: 'planting' }
  | { kind: 'correct'; plant: PlantStateWire }
  | { kind: 'photo'; plant: PlantStateWire }
  | null;

export default function FieldBedSheet({ bed, online, onClose, onChanged, onPlanChanged }: FieldBedSheetProps) {
  const { t, i18n } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const { handleError } = useApiError();
  const notification = useNotification();
  const { offerUndo } = useUndoSnackbar();
  const sheet = useBedSheet(bed.key);
  const [overlay, setOverlay] = useState<Overlay>(null);
  const [saving, setSaving] = useState(false);
  const lastDoneTapAt = useRef(0);
  const lastWriteTapAt = useRef(0);
  const savingRef = useRef(false);
  const titleId = `field-sheet-title-${bed.key}`;

  const { reload } = sheet;
  const changed = useCallback(() => {
    reload();
    onChanged();
  }, [reload, onChanged]);
  /** Planting and a position correction also change the plan's geometry and plants: the map reloads too. */
  const plantsChanged = useCallback(() => {
    changed();
    onPlanChanged();
  }, [changed, onPlanChanged]);

  const ready = sheet.state.status === 'ready' ? sheet.state : null;
  const sections = useMemo(() => fieldTaskSections(ready?.tasks ?? [], todayUtc()), [ready]);
  const groups = useMemo(
    () => (ready && ready.plants !== null ? groupPlants(ready.plants, i18n.language) : ready ? null : []),
    [ready, i18n.language],
  );
  const plantNames = useMemo(
    () => new Map((ready?.plants ?? []).map((plant) => [plant.plant_key, plant.instance_id])),
    [ready],
  );
  const context = useMemo<CareContext>(() => ({ locationTypeKey: bed.location_type_key }), [bed.location_type_key]);
  const taskName = (task: CareTask) => careTaskName(task, i18n.language);
  const categoryLabel = (category: string) => careCategoryLabel(t, category);

  /**
   * The double-tap guard (GP-UX-023, R-029): "Done" has its own clock, "Finish" and the one-tap chips share
   * one - a tap within 300 ms of the last on the same control, or while a write waits, is the same tap.
   */
  const claimTap = (last: { current: number }): boolean => {
    const now = Date.now();
    if (isDuplicateTap(last.current, now, savingRef.current)) return false;
    last.current = now;
    return true;
  };
  const begin = () => {
    savingRef.current = true;
    setSaving(true);
  };
  const end = () => {
    savingRef.current = false;
    setSaving(false);
  };

  const openDone = (task: CareTask) => {
    if (!online || !claimTap(lastDoneTapAt)) return;
    setOverlay({ kind: 'complete', task });
  };

  const complete = async (task: CareTask, payload: CompletionPayload) => {
    if (!online || !claimTap(lastWriteTapAt)) return;
    begin();
    try {
      await completeBedTask(task.key, payload);
      setOverlay(null);
      changed();
      offerUndo({
        message: t('pages.bed.care.undo.completed', { name: taskName(task) }),
        undo: async () => {
          await reopenWithUndo(task.key);
        },
        onUndone: changed,
      });
    } catch (error) {
      handleError(error);
    } finally {
      end();
    }
  };

  const offerLogUndo = (event: CareEventRef, label: string) => {
    onChanged();
    offerUndo({
      message: t('pages.bed.care.undo.logged', { category: label }),
      undo: () => voidCareEvent(event.key),
      onUndone: changed,
    });
  };

  const logChip = async (category: string) => {
    if (!online || !claimTap(lastWriteTapAt)) return;
    begin();
    const label = categoryLabel(category);
    try {
      const event = await logCareEvent(quickLogBody(bed.key, category, label, new Date()));
      offerLogUndo(event, label);
    } catch (error) {
      handleError(error);
    } finally {
      end();
    }
  };

  const onChip = (chip: QuickChip) => {
    if (chip.action === 'log' && chip.category) void logChip(chip.category);
    else if (chip.action === 'form' && chip.category) setOverlay({ kind: 'form', category: chip.category });
    else if (chip.action === 'planting') setOverlay({ kind: 'planting' });
  };

  const closeOverlay = () => setOverlay(null);
  const writesLocked = saving || !online;

  return (
    <Drawer
      anchor="bottom"
      open
      onClose={onClose}
      slotProps={{
        paper: {
          role: 'dialog',
          'aria-modal': true,
          'aria-labelledby': titleId,
          sx: { maxHeight: '90vh', borderTopLeftRadius: 12, borderTopRightRadius: 12 },
        },
      }}
      data-testid="field-bed-sheet"
    >
      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 3, fontSize: '1rem' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography id={titleId} variant="h5" component="h2" sx={{ flexGrow: 1, overflowWrap: 'anywhere' }}>
            {bed.name}
          </Typography>
          <IconButton
            onClick={onClose}
            aria-label={t('pages.gardenPlan.field.sheet.close')}
            sx={{ width: KIOSK_TOUCH_TARGET, height: KIOSK_TOUCH_TARGET, border: 2, borderColor: 'divider' }}
            data-testid="field-sheet-close"
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {!online && (
          <Alert severity="warning" data-testid="field-sheet-offline">
            {t('pages.gardenPlan.field.offline')}
          </Alert>
        )}

        {sheet.state.status === 'loading' && (
          <Box role="status" aria-busy="true" aria-label={t('pages.gardenPlan.field.sheet.loading')}>
            <LoadingSkeleton variant="card" />
          </Box>
        )}
        {sheet.state.status === 'error' && <ErrorDisplay error={sheet.state.message} onRetry={reload} />}

        {canEdit && (
          <QuickProtocolChips
            disabled={writesLocked}
            plantingAvailable={Boolean(bed.geometry)}
            onChip={onChip}
          />
        )}

        {ready && (
          <FieldTaskSection
            sections={sections}
            plantNames={plantNames}
            canEdit={canEdit}
            locked={writesLocked}
            onDone={openDone}
          />
        )}

        {ready && (
          <FieldPlantSection
            groups={groups}
            canEdit={canEdit}
            offline={!online}
            canCorrect={Boolean(bed.geometry)}
            onCorrect={(plant) => setOverlay({ kind: 'correct', plant })}
            onPhoto={(plant) => setOverlay({ kind: 'photo', plant })}
          />
        )}
      </Box>

      {overlay?.kind === 'complete' && (
        <CareCompletionDialog
          category={overlay.task.category}
          subject={taskName(overlay.task)}
          saving={saving}
          onSubmit={(payload) => void complete(overlay.task, payload)}
          onClose={closeOverlay}
          touchTarget={KIOSK_TOUCH_TARGET}
          submitLabel={t('pages.gardenPlan.field.finish')}
        />
      )}
      <Suspense fallback={null}>
        {overlay?.kind === 'form' && (
          <CareLogDialog
            bedKey={bed.key}
            context={context}
            fixedCategory={overlay.category}
            touchTarget={KIOSK_TOUCH_TARGET}
            onClose={closeOverlay}
            onLogged={(event, label) => {
              setOverlay(null);
              offerLogUndo(event, label);
            }}
          />
        )}
        {overlay?.kind === 'planting' && bed.geometry && (
          <PlantingDialog
            bedKey={bed.key}
            bedName={bed.name}
            geometry={bed.geometry}
            sunExposure={bed.sun_exposure}
            initialAlreadyPlanted
            touchTarget={KIOSK_TOUCH_TARGET}
            onClose={closeOverlay}
            onPlanted={(result) => {
              setOverlay(null);
              plantsChanged();
              notification.success(t('pages.gardenPlan.field.planted', { count: result.plantCount }));
            }}
          />
        )}
        {overlay?.kind === 'correct' && bed.geometry && overlay.plant.slot_key && (
          <PositionCorrectionDialog
            bedName={bed.name}
            bedGeometry={bed.geometry}
            bedKey={bed.key}
            slotKey={overlay.plant.slot_key}
            plantLabel={overlay.plant.instance_id}
            stepCm={FIELD_STEP_CM}
            showBigSteps={false}
            touchTarget={KIOSK_TOUCH_TARGET}
            dragHoldMs={FIELD_LONG_PRESS_MS}
            onClose={closeOverlay}
            onCorrected={() => {
              notification.success(t('pages.bed.planting.position.done', { plant: overlay.plant.instance_id }));
              setOverlay(null);
              plantsChanged();
            }}
          />
        )}
        {overlay?.kind === 'photo' && (
          <PlantPhotoUploadDialog
            open
            plantInstanceKey={overlay.plant.plant_key}
            touchTarget={KIOSK_TOUCH_TARGET}
            onClose={closeOverlay}
            onUploaded={() => {
              notification.success(t('pages.gardenPlan.field.photoSaved', { plant: overlay.plant.instance_id }));
              setOverlay(null);
            }}
          />
        )}
      </Suspense>
    </Drawer>
  );
}
