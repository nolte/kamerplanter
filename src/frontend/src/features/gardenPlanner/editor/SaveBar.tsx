/**
 * The save group of the plan editor (REQ-053 GP-NFR-005/006, GP-FR-026/155, GP-UX-017): undo and redo,
 * the save status ("Unsaved changes (n)" / "Saved" / failed), the auto-save switch and the save button.
 * Since wave 10 it is a part of the one editor header bar (§17.3, GP-UX-063): it never wraps, "Save" is
 * always shown, the auto-save switch is the first control the bar moves into its overflow, and below md
 * the status is compact (icon and count, the full words for screen readers) while undo and redo stand in
 * the `TouchBar` (`UndoRedoButtons`). A refused save (422) or a lost connection is explained below the
 * header bar by `SaveMessages`; `pending` is untouched then, so the user can fix the cause and save again.
 */
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import Tooltip from '@mui/material/Tooltip';
import { visuallyHidden } from '@mui/utils';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import ErrorOutlinedIcon from '@mui/icons-material/ErrorOutlined';
import RedoIcon from '@mui/icons-material/Redo';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import UndoIcon from '@mui/icons-material/Undo';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import type { PlanSaveFailure } from '../api/gardenPlan';
import type { PlanOperation } from '../model/types';
import {
  redo,
  saveGardenPlan,
  selectCanRedo,
  selectCanUndo,
  selectGardenPlanState,
  selectRedoLabel,
  selectUndoLabel,
  undo,
} from '../state/gardenPlanSlice';
import { failureHint, failureTitle, findingLines, knownCodeText } from './saveMessages';
import type { AutoSave } from './useAutoSave';

const PREFIX = 'pages.gardenPlan.editor.save';
// UI-NFR-001 R-011: below md undo and redo are touch targets in the TouchBar (AC-9), the header bar keeps the same size.
const TARGET_PX = 48;

type Refusal = Exclude<PlanSaveFailure, { kind: 'conflict' }>;

/** The operations a refusal belongs to: its findings index into exactly the list that was sent. */
interface FailureSnapshot {
  failure: Refusal;
  ops: PlanOperation[];
}

/** Undo and redo, 44 px each, their tooltip naming the action they would take back or repeat. */
export function UndoRedoButtons() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const canUndo = useAppSelector(selectCanUndo);
  const canRedo = useAppSelector(selectCanRedo);
  const undoLabel = useAppSelector(selectUndoLabel);
  const redoLabel = useAppSelector(selectRedoLabel);
  const onUndo = useCallback(() => void dispatch(undo()), [dispatch]);
  const onRedo = useCallback(() => void dispatch(redo()), [dispatch]);

  const action = (key: 'undo' | 'redo', label: string | null) => {
    const base = t(`${PREFIX}.${key}.label`);
    return label ? t(`${PREFIX}.${key}.withAction`, { action: t(label, { defaultValue: label }) }) : base;
  };
  const undoText = action('undo', undoLabel);
  const redoText = action('redo', redoLabel);
  return (
    <>
      <Tooltip title={undoText}>
        <span>
          <IconButton
            onClick={onUndo}
            disabled={!canUndo}
            aria-label={undoText}
            aria-keyshortcuts="Control+Z Meta+Z"
            data-testid="garden-plan-undo"
            sx={{ width: TARGET_PX, height: TARGET_PX }}
          >
            <UndoIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={redoText}>
        <span>
          <IconButton
            onClick={onRedo}
            disabled={!canRedo}
            aria-label={redoText}
            aria-keyshortcuts="Control+Shift+Z Meta+Shift+Z Control+Y"
            data-testid="garden-plan-redo"
            sx={{ width: TARGET_PX, height: TARGET_PX }}
          >
            <RedoIcon />
          </IconButton>
        </span>
      </Tooltip>
    </>
  );
}

/** Where saving stands: the words the status shows, and what the button may do. */
function useSaveStatus() {
  const { t } = useTranslation();
  const { pending, saveStatus } = useAppSelector(selectGardenPlanState);
  const count = pending.length;
  const saving = saveStatus === 'saving';
  const conflict = saveStatus === 'conflict';
  // Once everything pending is undone there is nothing left to retry: the old refusal is history.
  const failed = saveStatus === 'error' && count > 0;
  let statusText: string;
  if (saving) statusText = t(`${PREFIX}.status.saving`);
  else if (conflict) statusText = t(`${PREFIX}.status.conflict`);
  else if (failed) statusText = t(`${PREFIX}.status.failed`, { count });
  else if (count > 0) statusText = t(`${PREFIX}.status.dirty`, { count });
  else statusText = t(`${PREFIX}.status.saved`);
  return { count, saving, conflict, failed, statusText };
}

interface SaveBarProps {
  autoSave: AutoSave;
  /** Below md: the status is an icon with the count (the words stay for screen readers). */
  compact?: boolean;
  /** Undo and redo; below md they stand in the `TouchBar` instead (GP-UX-052). */
  showUndoRedo?: boolean;
  /** The auto-save switch; the header bar moves it into its overflow first (GP-UX-063 step 1). */
  showAutoSave?: boolean;
}

export function SaveBar({ autoSave, compact = false, showUndoRedo = true, showAutoSave = true }: SaveBarProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { count, saving, conflict, failed, statusText } = useSaveStatus();
  const save = useCallback(() => void dispatch(saveGardenPlan()), [dispatch]);

  return (
    <Box
      role="group"
      aria-label={t(`${PREFIX}.label`)}
      data-testid="garden-plan-save-bar"
      sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'nowrap', flexShrink: 0 }}
    >
      {showUndoRedo && <UndoRedoButtons />}
      <Box
        data-testid="garden-plan-save-status"
        data-pending-count={count}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          minWidth: 0,
          px: compact ? 0.5 : 1,
          whiteSpace: 'nowrap',
          typography: 'body2',
          // warning.main on paper is 3.1:1 in the light theme (see theme.ts): its dark tone is used there.
          color: (theme) =>
            failed || conflict
              ? theme.palette.error.main
              : count > 0
                ? theme.palette.mode === 'light'
                  ? theme.palette.warning.dark
                  : theme.palette.warning.main
                : theme.palette.text.secondary,
        }}
      >
        {failed || conflict ? (
          <ErrorOutlinedIcon fontSize="small" aria-hidden />
        ) : count === 0 && !saving ? (
          <CheckCircleOutlinedIcon fontSize="small" aria-hidden />
        ) : compact ? (
          <EditNoteOutlinedIcon fontSize="small" aria-hidden />
        ) : null}
        {compact ? (
          <>
            {/* The words are for screen readers; the eye reads the icon and the count (GP-UX-063 below md). */}
            <Box component="span" sx={visuallyHidden}>
              {statusText}
            </Box>
            {count > 0 && (
              <Box component="span" aria-hidden data-testid="garden-plan-save-status-count">
                {count}
              </Box>
            )}
          </>
        ) : (
          <span>{statusText}</span>
        )}
      </Box>
      {showAutoSave && (
        <FormControlLabel
          sx={{ m: 0, minHeight: TARGET_PX, typography: 'body2', whiteSpace: 'nowrap' }}
          control={
            <Switch
              size="small"
              checked={autoSave.enabled}
              onChange={(event) => autoSave.setEnabled(event.target.checked)}
              slotProps={{ input: { 'data-testid': 'garden-plan-autosave' } as object }}
            />
          }
          label={t(`${PREFIX}.autoSave.label`)}
        />
      )}
      <Tooltip title={t(`${PREFIX}.shortcut`)}>
        <span>
          <Button
            variant="contained"
            onClick={save}
            disabled={count === 0 || saving || conflict}
            aria-busy={saving}
            aria-keyshortcuts="Control+S Meta+S"
            startIcon={
              saving ? <CircularProgress size={18} color="inherit" /> : <SaveOutlinedIcon />
            }
            sx={{ minHeight: TARGET_PX, whiteSpace: 'nowrap' }}
            data-testid="garden-plan-save"
          >
            {failed ? t(`${PREFIX}.retry`) : t(`${PREFIX}.button`)}
          </Button>
        </span>
      </Tooltip>
    </Box>
  );
}

/**
 * What saving has to say below the header bar: the spoken "Saved", the paused auto-save and a refused save with
 * its findings. Kept apart from the bar, so the bar stays one line (GP-UX-063).
 */
export function SaveMessages({ autoSave }: { autoSave: AutoSave }) {
  const { t } = useTranslation();
  const { plan, pending, saveStatus, saveFailure } = useAppSelector(selectGardenPlanState);
  const { count, saving, conflict, failed } = useSaveStatus();

  // Keep the operations of the request that failed: the user may edit on before reading the message,
  // and "change 3" must still mean the third operation of that request. (State adjusted during
  // render, the documented derived-state pattern.)
  const [snapshot, setSnapshot] = useState<FailureSnapshot | null>(null);
  if (saveFailure === null) {
    if (snapshot !== null) setSnapshot(null);
  } else if (snapshot?.failure !== saveFailure) {
    setSnapshot({ failure: saveFailure, ops: pending.map((item) => item.op) });
  }

  // "Saved" is spoken once, when a save has just finished with nothing left to send; the next edit
  // clears it (state adjusted during render, no effect between the store and the region).
  const [wasSaving, setWasSaving] = useState(false);
  const [savedSpoken, setSavedSpoken] = useState(false);
  if (saving !== wasSaving) {
    setWasSaving(saving);
    if (wasSaving && saveStatus === 'idle' && count === 0) setSavedSpoken(true);
  } else if (savedSpoken && count > 0) {
    setSavedSpoken(false);
  }

  const lines = useMemo(
    () =>
      snapshot && plan
        ? findingLines(snapshot.failure.kind === 'rejected' ? snapshot.failure.findings : [], snapshot.ops, plan, t)
        : [],
    [plan, snapshot, t],
  );

  const refusal = failed && snapshot ? snapshot.failure : null;

  return (
    <Box data-testid="garden-plan-save-area" sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {/* The one spoken word of the bar: undo, redo and every edit are said by the editor's live region,
          a refusal by the alert below, the conflict by its dialog - only a successful save is said here. */}
      <Box
        role="status"
        aria-live="polite"
        aria-atomic="true"
        sx={visuallyHidden}
        data-testid="garden-plan-save-announcement"
      >
        {savedSpoken ? t(`${PREFIX}.status.saved`) : ''}
      </Box>
      {autoSave.paused && (
        <Box
          role="status"
          data-testid="garden-plan-autosave-paused"
          sx={{ typography: 'body2', color: 'text.secondary', px: 1 }}
        >
          {t(`${PREFIX}.autoSave.${conflict ? 'pausedConflict' : 'pausedFailed'}`)}
        </Box>
      )}
      {refusal && (
        <Alert severity="error" role="alert" data-testid="garden-plan-save-error">
          <Box sx={{ fontWeight: 600 }}>{failureTitle(refusal, t)}</Box>
          {lines.length > 0 ? (
            <Box component="ul" sx={{ m: 0, pl: 2.5 }} data-testid="garden-plan-save-findings">
              {lines.map((line) => (
                <li key={line.id}>{line.text}</li>
              ))}
            </Box>
          ) : (
            refusal.kind === 'rejected' && knownCodeText(refusal.code, t) && (
              <Box>{knownCodeText(refusal.code, t)}</Box>
            )
          )}
          <Box>{failureHint(refusal, t)}</Box>
        </Alert>
      )}
    </Box>
  );
}
