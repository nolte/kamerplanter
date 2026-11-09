/**
 * The bed sheet of field mode (REQ-053 §18.1 steps 3-9, GP-UX-023/025/029, GP-FR-149): a bottom sheet
 * with the bed's name, the quick protocol, the tasks (overdue first) and the plants. Everything appears
 * on a tap - there is no hover in the field (GP-UX-025) - and every action is sent at once, there is no
 * dirty state (GP-UX-003, F-16).
 *
 * "Done" → short dialog → "Finish" is two taps after the bed was chosen (GP-ACC-029). A second tap within
 * 300 ms, or while the first is waiting for its answer, is the same tap. Every write offers "Undo" for 8 s.
 *
 * Offline (REQ-053 WP 9.4, GP-UX-024 part 2): "Done", the note and the photos go into the offline write buffer
 * (`offline/bufferedWrite.ts`) and are sent with their capture time once the connection is back; "Undo" then
 * takes the entry out of the buffer. Everything else — the one-tap chips, harvest, planting, a position
 * correction, sun and site — stays online-only. Without a usable buffer (no IndexedDB, kill switch) every write
 * stays locked offline, as before wave 9 (D-23).
 *
 * A photo goes to the bed or to a plant (§18.1 step 7, GP-FR-051): "Photo of the bed" stores it in the bed's
 * gallery (the first one becomes the cover shown beside the name), "Photo" at a plant in that plant's gallery.
 */
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import CloseIcon from '@mui/icons-material/Close';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { useBedSiteFeatures } from '../planting/useBedSiteFeatures';
import BedCoverPhoto from '../bed/BedCoverPhoto';
import { addBedPhoto } from '../bed/bedPhotoApi';
import { bedPhotoUploadError } from '../bed/bedPhotoMessages';
import type { BedListItem } from '../bed/types';
import { uploadPlantPhoto } from '@/api/endpoints/plantPhotos';
import { completeBedTask, logCareEvent, reopenWithUndo, voidCareEvent } from '../care/careApi';
import { NOTE_CATEGORY, type CareContext } from '../care/careCategories';
import { careCategoryLabel, careTaskName } from '../care/careLabels';
import CareCompletionDialog from '../care/CareCompletionDialog';
import type { CareEventBody, CareEventRef, CareTask, CompletionPayload } from '../care/careTypes';
import { isDuplicateTap } from '../care/submitGuard';
import { useUndoSnackbar } from '../care/useUndoSnackbar';
import type { PlantStateWire } from '../planting/plantStateApi';
import { fieldTaskSections, todayUtc } from './fieldDue';
import { groupPlants } from './fieldPlants';
import FieldPlantSection from './FieldPlantSection';
import FieldSiteSection from './FieldSiteSection';
import FieldSunSection from './FieldSunSection';
import FieldTaskSection from './FieldTaskSection';
import QuickProtocolChips from './QuickProtocolChips';
import { quickLogBody, type QuickChip, type QuickChipId } from './quickChips';
import { useBedSheet } from './useBedSheet';
import CachedDataBanner from '../offline/CachedDataBanner';
import OfflineCacheMiss from '../offline/OfflineCacheMiss';
import { useCacheScope } from '../offline/useCacheScope';
import { useReloadOnReconnect } from '../offline/useReloadOnReconnect';
import { canBuffer, sendOrBuffer, type BufferTarget } from '../offline/bufferedWrite';
import { QUEUE_CAPACITY, isPerformedTooOld, isQueueFull } from '../offline/queue';
import { photoAsSent, photoForQueue, withGenericName } from '../offline/queuedPhoto';
import { useQueuedUndo } from '../offline/useQueuedUndo';
// The direct send carries the same per-request timeouts as the sync (review B2): a hanging request ends as a
// network failure, so the buffer fallback with the same id is reached.
import { PHOTO_SEND_TIMEOUT_MS, SEND_TIMEOUT_MS } from '../offline/sync';
import type { QueuedWrite, StoredPhoto } from '../offline/queueTypes';
import { preloadOfflineCapture } from '../offline/preloadOfflineCapture';
import { useWriteQueue } from '../offline/useWriteQueue';

const CareLogDialog = lazy(() => import('../care/CareLogDialog'));
const PlantingDialog = lazy(() => import('../planting/PlantingDialog'));
const PositionCorrectionDialog = lazy(() => import('../planting/PositionCorrectionDialog'));
const PlantPhotoUploadDialog = lazy(() => import('@/components/photos/PlantPhotoUploadDialog'));

/** Offline with the buffer, only the note chip works (the other chips need the server). */
const BUFFERED_CHIPS: ReadonlySet<QuickChipId> = new Set<QuickChipId>(['note']);

/** Lie-fi: the first and the longest wait before the cached sheet is read again while the browser says online. */
export const SHEET_RETRY_FIRST_MS = 2000;
export const SHEET_RETRY_MAX_MS = 60_000;

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
  | { kind: 'bedPhoto' }
  | null;

export default function FieldBedSheet({ bed, online, onClose, onChanged, onPlanChanged }: FieldBedSheetProps) {
  const { t, i18n } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const bedSite = useBedSiteFeatures(bed);
  const { handleError } = useApiError();
  const notification = useNotification();
  const { offerUndo } = useUndoSnackbar();
  const scope = useCacheScope();
  const { offerQueuedUndo } = useQueuedUndo(scope);
  const sheet = useBedSheet(bed.key, scope);
  const queue = useWriteQueue(scope);
  const [overlay, setOverlay] = useState<Overlay>(null);
  const [saving, setSaving] = useState(false);
  const lastDoneTapAt = useRef(0);
  const lastWriteTapAt = useRef(0);
  const savingRef = useRef(false);
  const titleId = `field-sheet-title-${bed.key}`;

  const { reload } = sheet;
  // A cached sheet or an offline miss is read again once the connection is back: the write lock clears (C3).
  useReloadOnReconnect(
    (sheet.state.status === 'ready' && sheet.state.cachedAt !== null) ||
      (sheet.state.status === 'error' && sheet.state.offlineMiss),
    reload,
  );
  const changed = useCallback(() => {
    reload();
    onChanged();
  }, [reload, onChanged]);

  // Lie-fi: online, yet the sheet is the cached one — `useReloadOnReconnect` never fires (nothing flips), so the
  // read is retried with a backoff (2 s, 4 s … 60 s) until the server answers.
  const staleWhileOnline = online && sheet.state.status === 'ready' && sheet.state.cachedAt !== null;
  const retryDelay = useRef(SHEET_RETRY_FIRST_MS);
  useEffect(() => {
    if (!staleWhileOnline) {
      retryDelay.current = SHEET_RETRY_FIRST_MS;
      return undefined;
    }
    if (sheet.reloading) return undefined;
    const timer = setTimeout(reload, retryDelay.current);
    retryDelay.current = Math.min(SHEET_RETRY_MAX_MS, retryDelay.current * 2);
    return () => clearTimeout(timer);
  }, [staleWhileOnline, sheet.reloading, reload]);
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
  const context = useMemo<CareContext>(
    () => ({ locationTypeKey: bed.location_type_key, areaM2: bed.area_m2 ?? null }),
    [bed.location_type_key, bed.area_m2],
  );
  const taskName = (task: CareTask) => careTaskName(task, i18n.language);
  const categoryLabel = (category: string) => careCategoryLabel(t, category);

  // ── The offline write buffer (WP 9.4) ──
  const bufferOn = queue.available && canBuffer(scope);
  // The first offline capture must not need a chunk download (`preloadOfflineCapture`): loaded while online, again
  // after a reconnect when a load failed. `captureReady` is the sheet's signal that an offline capture can work.
  const [captureReady, setCaptureReady] = useState(false);
  useEffect(() => {
    if (!bufferOn || !online) return undefined;
    let cancelled = false;
    void preloadOfflineCapture().then((ready) => {
      if (!cancelled && ready) setCaptureReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [bufferOn, online]);
  const target: BufferTarget = {
    scope,
    // A sheet from the cache (lie-fi) buffers like offline: no direct send against a snapshot.
    online: online && (sheet.state.status !== 'ready' || sheet.state.cachedAt === null),
    bedKey: bed.key,
    bedName: bed.name,
  };
  const queuedTaskKeys = useMemo(
    // Only what is still on its way hides "Done": a failed or conflicting completion shows its own state in the
    // dialog and must not lock the task for good.
    () =>
      new Set(
        queue.entries.flatMap((entry) =>
          entry.write.kind === 'complete' && (entry.status === 'pending' || entry.status === 'syncing')
            ? [entry.write.taskKey]
            : [],
        ),
      ),
    [queue.entries],
  );
  // An entry of this bed left the buffer (sent or discarded): what the server has now is read again.
  const bedEntryCount = queue.entries.filter((entry) => entry.bedKey === bed.key).length;
  const lastBedEntryCount = useRef(bedEntryCount);
  useEffect(() => {
    if (bedEntryCount < lastBedEntryCount.current && online) changed();
    lastBedEntryCount.current = bedEntryCount;
  }, [bedEntryCount, online, changed]);
  /** The last photo went into the buffer, not to the server (the confirmation says so). */
  const photoQueued = useRef(false);

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

  // A sheet read from the plan cache is a past state: nothing is written against it (WP 9.2) — except what the
  // buffer takes, which the server checks on arrival (a closed task is a conflict, WP 9.3).
  const writesLocked = saving || !online || (ready?.cachedAt ?? null) !== null;
  // Online with a sheet from the plan cache (WP 9.2): the lock stays — the sheet reloads first; nothing is sent
  // or buffered against a snapshot while the server is reachable.
  const fromCache = (ready?.cachedAt ?? null) !== null;
  // The sheet came from the plan cache although the browser says online (lie-fi: the read got no answer). A write
  // is then made against the capture-time view the user sees — exactly what offline buffering is for — so it is
  // BUFFERED, never sent directly against the snapshot (WP 9.2). Locked only while a reload is on its way.
  const sendDirect = online && !fromCache;
  const bufferedLocked = bufferOn
    ? saving || (!sendDirect && queue.full) || (online && fromCache && sheet.reloading)
    : writesLocked;

  const bufferError = (error: unknown) => {
    if (isQueueFull(error)) notification.warning(t('pages.gardenPlan.field.buffer.full', { max: QUEUE_CAPACITY }));
    else if (isPerformedTooOld(error)) notification.warning(t('pages.gardenPlan.field.buffer.tooOld'));
    else handleError(error);
  };

  const openDone = (task: CareTask) => {
    if (bufferedLocked || queuedTaskKeys.has(task.key) || !claimTap(lastDoneTapAt)) return;
    setOverlay({ kind: 'complete', task });
  };

  const complete = async (task: CareTask, payload: CompletionPayload) => {
    if (bufferedLocked || !claimTap(lastWriteTapAt)) return;
    begin();
    // The capture time travels with the entry (GP-UX-024); the online attempt sends the same body, so a resend
    // with its id is a replay and never a `payload_mismatch`.
    const sent: CompletionPayload = bufferOn ? { ...payload, performed_at: payload.performed_at ?? new Date().toISOString() } : payload;
    try {
      const outcome = await sendOrBuffer(
        target,
        () => ({ kind: 'complete', taskKey: task.key, taskName: taskName(task), payload: sent }),
        (id) => completeBedTask(task.key, sent, id, { timeout: SEND_TIMEOUT_MS }),
      );
      setOverlay(null);
      if (outcome.status === 'queued') {
        offerQueuedUndo(outcome.entry, t('pages.gardenPlan.field.buffer.completed', { name: taskName(task) }));
        return;
      }
      changed();
      offerUndo({
        message: t('pages.bed.care.undo.completed', { name: taskName(task) }),
        undo: async () => {
          await reopenWithUndo(task.key);
        },
        onUndone: changed,
      });
    } catch (error) {
      bufferError(error);
    } finally {
      end();
    }
  };

  /** The note chip's short form (GP-UX-029): sent, or buffered offline. */
  const logNote = async (body: CareEventBody, label: string) => {
    try {
      const outcome = await sendOrBuffer(target, () => ({ kind: 'note', body }), (id) => logCareEvent(body, id, { timeout: SEND_TIMEOUT_MS }));
      setOverlay(null);
      if (outcome.status === 'queued') {
        offerQueuedUndo(outcome.entry, t('pages.gardenPlan.field.buffer.noted'));
      } else {
        offerLogUndo(outcome.result, label);
      }
    } catch (error) {
      bufferError(error);
    }
  };

  /**
   * A photo of the bed or a plant. Online it goes as the upload dialog prepared it (the gallery's single encode,
   * 2048 px / JPEG 90). Only what is buffered is re-encoded for the device (≤ 1920 px, JPEG 80, R-044) — a capture
   * made offline. A buffered copy of an online attempt whose answer got lost keeps the bytes that were sent: the
   * resend under the same id must carry the same file, or it would be a `payload_mismatch`.
   */
  const sendPhoto = async (
    file: File,
    write: (photo: StoredPhoto) => QueuedWrite,
    direct: (file: File, id: string | undefined) => Promise<unknown>,
  ): Promise<void> => {
    const sent = bufferOn ? withGenericName(file) : file;
    const outcome = await sendOrBuffer(
      target,
      async (fallback) => {
        if (fallback) return write(await photoAsSent(sent));
        try {
          return write(await photoForQueue(file));
        } catch {
          throw new Error(t('pages.gardenPlan.field.buffer.photoUnreadable'));
        }
      },
      (id) => direct(sent, id),
    );
    photoQueued.current = outcome.status === 'queued';
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

  const uploadBedPhoto = (file: File) =>
    sendPhoto(
      file,
      (photo) => ({ kind: 'bedPhoto', locationKey: bed.key, photo }),
      (sent, id) => addBedPhoto(bed.key, sent, id, { timeout: PHOTO_SEND_TIMEOUT_MS }),
    );
  /** The photo of the plant the photo dialog was opened for. */
  const uploadPhotoOfPlant = (file: File): Promise<void> => {
    if (overlay?.kind !== 'photo') return Promise.resolve();
    const { plant_key: plantKey, instance_id: plantName } = overlay.plant;
    return sendPhoto(
      file,
      (photo) => ({ kind: 'plantPhoto', plantKey, plantName, photo }),
      (sent, id) => uploadPlantPhoto(plantKey, sent, id, { timeout: PHOTO_SEND_TIMEOUT_MS }),
    );
  };
  const fullMessage = (error: unknown): string | null =>
    isQueueFull(error) ? t('pages.gardenPlan.field.buffer.full', { max: QUEUE_CAPACITY }) : null;
  const bedPhotoError = useCallback(
    (error: unknown) =>
      isQueueFull(error) ? t('pages.gardenPlan.field.buffer.full', { max: QUEUE_CAPACITY }) : bedPhotoUploadError(t, error),
    [t],
  );

  const closeOverlay = () => setOverlay(null);
  const chipsDisabled = writesLocked && (!bufferOn || bufferedLocked);
  const onlyChips = writesLocked && bufferOn && !bufferedLocked ? BUFFERED_CHIPS : undefined;
  const bufferedOffline = !online && bufferOn;

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
      data-offline-capture-ready={captureReady ? 'true' : 'false'}
    >
      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 3, fontSize: '1rem' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BedCoverPhoto
            coverPhotoRef={bed.cover_photo_ref}
            bedName={bed.name}
            sx={{ width: KIOSK_TOUCH_TARGET, height: KIOSK_TOUCH_TARGET }}
            testId="field-sheet-cover"
          />
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
            {bufferedOffline ? t('pages.gardenPlan.field.buffer.offline') : t('pages.gardenPlan.field.offline')}
          </Alert>
        )}
        {bufferOn && queue.full && (
          <Alert severity="warning" data-testid="field-sheet-buffer-full">
            {t('pages.gardenPlan.field.buffer.full', { max: QUEUE_CAPACITY })}
          </Alert>
        )}

        {sheet.state.status === 'loading' && (
          <Box role="status" aria-busy="true" aria-label={t('pages.gardenPlan.field.sheet.loading')}>
            <LoadingSkeleton variant="card" />
          </Box>
        )}
        {sheet.state.status === 'ready' && sheet.state.cachedAt !== null && (
          <CachedDataBanner cachedAt={sheet.state.cachedAt} testId="field-sheet-cached-banner" />
        )}
        {sheet.state.status === 'error' && sheet.state.offlineMiss && (
          <OfflineCacheMiss subject="bed" testId="field-sheet-offline-miss" onRetry={reload} />
        )}
        {sheet.state.status === 'error' && !sheet.state.offlineMiss && (
          <ErrorDisplay error={sheet.state.message} onRetry={reload} />
        )}

        {canEdit && (
          <QuickProtocolChips
            disabled={chipsDisabled}
            onlyChips={onlyChips}
            plantingAvailable={Boolean(bed.geometry)}
            onChip={onChip}
          />
        )}

        {canEdit && (
          <Box component="section" aria-labelledby={`field-photo-title-${bed.key}`} data-testid="field-bed-photo-section">
            <Typography id={`field-photo-title-${bed.key}`} variant="h6" component="h3" sx={{ mb: 0.5 }}>
              {t('pages.gardenPlan.field.bedPhoto.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.gardenPlan.field.bedPhoto.hint')}
            </Typography>
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<AddAPhotoIcon aria-hidden="true" />}
              onClick={() => setOverlay({ kind: 'bedPhoto' })}
              disabled={bufferOn ? bufferedLocked : !online}
              sx={{ minHeight: KIOSK_TOUCH_TARGET, minWidth: KIOSK_TOUCH_TARGET, borderWidth: 2 }}
              aria-label={t('pages.gardenPlan.field.bedPhoto.actionFor', { bed: bed.name })}
              data-testid="field-bed-photo"
            >
              {t('pages.gardenPlan.field.bedPhoto.action')}
            </Button>
          </Box>
        )}

        {ready && (
          <FieldTaskSection
            sections={sections}
            plantNames={plantNames}
            canEdit={canEdit}
            locked={bufferedLocked}
            queuedTaskKeys={queuedTaskKeys}
            onDone={openDone}
          />
        )}

        {ready && (
          <FieldPlantSection
            groups={groups}
            canEdit={canEdit}
            offline={!online}
            photoLocked={bufferOn ? bufferedLocked : !online}
            canCorrect={Boolean(bed.geometry)}
            onCorrect={(plant) => setOverlay({ kind: 'correct', plant })}
            onPhoto={(plant) => setOverlay({ kind: 'photo', plant })}
          />
        )}

        <FieldSunSection bed={bed} canEdit={canEdit} online={online} onChanged={onChanged} />
        <FieldSiteSection bed={bed} canEdit={canEdit} online={online} onChanged={onChanged} />
      </Box>

      {overlay?.kind === 'complete' && (
        <CareCompletionDialog
          category={overlay.task.category}
          subject={taskName(overlay.task)}
          areaM2={bed.area_m2 ?? null}
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
            logCare={overlay.category === NOTE_CATEGORY ? logNote : undefined}
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
            bedSite={bedSite}
            siteFlags={bed.site_conditions?.flags}
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
            // No stepCm: field mode moves by the dialog's own STEP_CM (10 cm, §18.1 step 9, F-16), one constant for
            // both modes; the fine steps are the desktop's choice and stay off here.
            showFineSteps={false}
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
            upload={uploadPhotoOfPlant}
            errorMessage={fullMessage}
            touchTarget={KIOSK_TOUCH_TARGET}
            onClose={closeOverlay}
            onUploaded={() => {
              notification.success(
                photoQueued.current
                  ? t('pages.gardenPlan.field.buffer.photoQueued')
                  : t('pages.gardenPlan.field.photoSaved', { plant: overlay.plant.instance_id }),
              );
              setOverlay(null);
            }}
          />
        )}
        {overlay?.kind === 'bedPhoto' && (
          <PlantPhotoUploadDialog
            open
            upload={uploadBedPhoto}
            title={t('pages.bed.photos.uploadTitle', { bed: bed.name })}
            errorMessage={bedPhotoError}
            photoTips={false}
            touchTarget={KIOSK_TOUCH_TARGET}
            onClose={closeOverlay}
            onUploaded={() => {
              if (photoQueued.current) {
                notification.success(t('pages.gardenPlan.field.buffer.photoQueued'));
                setOverlay(null);
                return;
              }
              notification.success(t('pages.gardenPlan.field.bedPhoto.saved', { bed: bed.name }));
              setOverlay(null);
              // The first photo becomes the cover; the list carries it.
              onChanged();
            }}
          />
        )}
      </Suspense>
    </Drawer>
  );
}
