/**
 * The save bar of the plan editor (REQ-053 GP-NFR-005/006, GP-FR-026/155, GP-UX-017): undo and redo,
 * the save status ("Unsaved changes (n)" / "Saved" / failed) and the save button. It stays visible on
 * every width - on a phone it is the only place for undo and redo, so the buttons are 44 px and
 * their tooltip names the action. A refused save (422) or a lost connection is explained below the
 * bar; `pending` is untouched then, so the user can fix the cause and save again.
 */
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
import { visuallyHidden } from '@mui/utils';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
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

const PREFIX = 'pages.gardenPlan.editor.save';
const TARGET_PX = 44;

type Refusal = Exclude<PlanSaveFailure, { kind: 'conflict' }>;

/** The operations a refusal belongs to: its findings index into exactly the list that was sent. */
interface FailureSnapshot {
  failure: Refusal;
  ops: PlanOperation[];
}

export function SaveBar() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { plan, pending, saveStatus, saveFailure } = useAppSelector(selectGardenPlanState);
  const canUndo = useAppSelector(selectCanUndo);
  const canRedo = useAppSelector(selectCanRedo);
  const undoLabel = useAppSelector(selectUndoLabel);
  const redoLabel = useAppSelector(selectRedoLabel);

  // Keep the operations of the request that failed: the user may edit on before reading the message,
  // and "change 3" must still mean the third operation of that request. (State adjusted during
  // render, the documented derived-state pattern.)
  const [snapshot, setSnapshot] = useState<FailureSnapshot | null>(null);
  if (saveFailure === null) {
    if (snapshot !== null) setSnapshot(null);
  } else if (snapshot?.failure !== saveFailure) {
    setSnapshot({ failure: saveFailure, ops: pending.map((item) => item.op) });
  }

  const count = pending.length;
  const saving = saveStatus === 'saving';
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
  const conflict = saveStatus === 'conflict';
  // Once everything pending is undone there is nothing left to retry: the old refusal is history.
  const failed = saveStatus === 'error' && count > 0;

  const save = useCallback(() => void dispatch(saveGardenPlan()), [dispatch]);
  const onUndo = useCallback(() => void dispatch(undo()), [dispatch]);
  const onRedo = useCallback(() => void dispatch(redo()), [dispatch]);

  const action = (key: 'undo' | 'redo', label: string | null) => {
    const base = t(`${PREFIX}.${key}.label`);
    return label ? t(`${PREFIX}.${key}.withAction`, { action: t(label, { defaultValue: label }) }) : base;
  };
  const undoText = action('undo', undoLabel);
  const redoText = action('redo', redoLabel);

  let statusText: string;
  if (saving) statusText = t(`${PREFIX}.status.saving`);
  else if (conflict) statusText = t(`${PREFIX}.status.conflict`);
  else if (failed) statusText = t(`${PREFIX}.status.failed`, { count });
  else if (count > 0) statusText = t(`${PREFIX}.status.dirty`, { count });
  else statusText = t(`${PREFIX}.status.saved`);

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
      <Paper
        variant="outlined"
        role="group"
        aria-label={t(`${PREFIX}.label`)}
        data-testid="garden-plan-save-bar"
        sx={{ display: 'flex', alignItems: 'center', gap: 0.5, p: 0.5, flexWrap: 'wrap' }}
      >
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
        <Box
          data-testid="garden-plan-save-status"
          data-pending-count={count}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            flexGrow: 1,
            minWidth: 0,
            px: 1,
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
          ) : null}
          <span>{statusText}</span>
        </Box>
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
              sx={{ minHeight: TARGET_PX }}
              data-testid="garden-plan-save"
            >
              {failed ? t(`${PREFIX}.retry`) : t(`${PREFIX}.button`)}
            </Button>
          </span>
        </Tooltip>
      </Paper>
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
