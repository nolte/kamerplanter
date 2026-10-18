/**
 * Complete one kind of task on several beds in one step (REQ-053 GP-FR-088): "all beds of the zone
 * are watered". Step one picks the kind and the beds and looks up the open tasks of that kind on them
 * (the beds' own tasks and those of their plants); step two takes the short care form once and sends
 * it with every task to `POST /tasks/batch/status`. At most 200 tasks per call; tasks the server
 * cannot complete are reported, the rest is done.
 */
import { useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import FormLabel from '@mui/material/FormLabel';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import type { BedListItem } from '../bed/types';
import { completeTasksBatch, getBedQueue, reopenWithUndo } from './careApi';
import { categoriesFor, formKindOf } from './careCategories';
import { buildCompletionPayload, defaultUnit, emptyForm, validateForm, type CareFormState } from './careForm';
import CareFormFields from './CareFormFields';
import type { CareTask } from './careTypes';
import { isDuplicateTap } from './submitGuard';
import { useUndoSnackbar } from './useUndoSnackbar';

/** GP-FR-088: tasks one batch may carry. */
export const MAX_BATCH_TASKS = 200;

interface BatchCompleteDialogProps {
  beds: readonly BedListItem[];
  onClose: () => void;
  /** Tasks were completed (or taken back); the list reloads its counters. */
  onChanged: () => void;
}

interface Found {
  tasks: CareTask[];
  bedCount: number;
  failedBeds: number;
}

export default function BatchCompleteDialog({ beds, onClose, onChanged }: BatchCompleteDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const { offerUndo } = useUndoSnackbar();
  const categories = useMemo(() => categoriesFor({}, 'task'), []);
  const [category, setCategory] = useState<string>('watering');
  const [selected, setSelected] = useState<ReadonlySet<string>>(
    () => new Set(beds.filter((bed) => (bed.open_task_count ?? 0) > 0).map((bed) => bed.key)),
  );
  const [busy, setBusy] = useState(false);
  const [found, setFound] = useState<Found | null>(null);
  const now = useMemo(() => new Date(), []);
  const [state, setState] = useState<CareFormState>(() => ({ ...emptyForm(now), unit: defaultUnit(formKindOf('watering')) }));
  const [showErrors, setShowErrors] = useState(false);
  const lastSubmitAt = useRef(0);
  const errors = showErrors ? validateForm(state, new Date()) : {};

  const toggle = (key: string) =>
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const changeCategory = (next: string) => {
    setCategory(next);
    setState((current) => ({ ...emptyForm(now), note: current.note, unit: defaultUnit(formKindOf(next)) }));
    setFound(null);
  };

  const find = async () => {
    setBusy(true);
    try {
      const keys = beds.filter((bed) => selected.has(bed.key)).map((bed) => bed.key);
      const results = await Promise.allSettled(keys.map((key) => getBedQueue(key, { category })));
      const byKey = new Map<string, CareTask>();
      let failedBeds = 0;
      for (const result of results) {
        if (result.status === 'rejected') failedBeds += 1;
        else for (const task of result.value) if (!task.suggested) byKey.set(task.key, task);
      }
      setFound({ tasks: [...byKey.values()], bedCount: keys.length - failedBeds, failedBeds });
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (found === null || isDuplicateTap(lastSubmitAt.current, Date.now(), busy)) return;
    if (Object.keys(validateForm(state, new Date())).length > 0) {
      setShowErrors(true);
      return;
    }
    lastSubmitAt.current = Date.now();
    setBusy(true);
    try {
      const keys = found.tasks.slice(0, MAX_BATCH_TASKS).map((task) => task.key);
      const result = await completeTasksBatch(keys, buildCompletionPayload(state, category));
      if (result.failed.length > 0) {
        notification.warning(
          t('pages.bed.care.batch.partial', { done: result.succeeded.length, failed: result.failed.length }),
        );
      }
      onChanged();
      if (result.succeeded.length > 0) {
        offerUndo({
          message: t('pages.bed.care.undo.batch', { count: result.succeeded.length }),
          undo: async () => {
            await Promise.all(result.succeeded.map((key) => reopenWithUndo(key)));
          },
          onUndone: onChanged,
        });
      }
      onClose();
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  };

  const categoryName = t(`enums.taskCategory.${category}`);
  const count = found ? Math.min(found.tasks.length, MAX_BATCH_TASKS) : 0;

  return (
    <Dialog
      open
      onClose={busy ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="care-batch-title"
      data-testid="care-batch-dialog"
    >
      <DialogTitle id="care-batch-title">{t('pages.bed.care.batch.title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        {found === null ? (
          <>
            <Typography variant="body2" color="text.secondary">
              {t('pages.bed.care.batch.intro')}
            </Typography>
            <TextField
              select
              label={t('pages.bed.care.batch.category')}
              value={category}
              onChange={(event) => changeCategory(event.target.value)}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
              slotProps={{ htmlInput: { 'data-testid': 'care-batch-category' } }}
            >
              {categories.map((value) => (
                <MenuItem key={value} value={value}>
                  {t(`enums.taskCategory.${value}`)}
                </MenuItem>
              ))}
            </TextField>
            <Box component="fieldset" sx={{ border: 0, p: 0, m: 0 }}>
              <FormLabel component="legend">{t('pages.bed.care.batch.beds')}</FormLabel>
              <FormGroup>
                {beds.map((bed) => (
                  <FormControlLabel
                    key={bed.key}
                    sx={{ minHeight: 44 }}
                    control={
                      <Checkbox
                        checked={selected.has(bed.key)}
                        onChange={() => toggle(bed.key)}
                        slotProps={{ input: { 'data-testid': `care-batch-bed-${bed.key}` } as object }}
                      />
                    }
                    label={bed.name}
                  />
                ))}
              </FormGroup>
              {selected.size === 0 && (
                <Typography variant="caption" color="text.secondary">
                  {t('pages.bed.care.batch.noBeds')}
                </Typography>
              )}
            </Box>
          </>
        ) : found.tasks.length === 0 ? (
          <Alert severity="info" data-testid="care-batch-none">
            {t('pages.bed.care.batch.none', { category: categoryName })}
          </Alert>
        ) : (
          <>
            <Typography variant="body1" data-testid="care-batch-found">
              {t('pages.bed.care.batch.found', { tasks: found.tasks.length, beds: found.bedCount })}
            </Typography>
            {found.failedBeds > 0 && <Alert severity="warning">{t('pages.bed.care.batch.findFailed')}</Alert>}
            {found.tasks.length > MAX_BATCH_TASKS && (
              <Alert severity="warning">{t('pages.bed.care.batch.tooMany', { max: MAX_BATCH_TASKS })}</Alert>
            )}
            <Typography variant="caption" color="text.secondary">
              {t('pages.bed.care.complete.optionalHint')}
            </Typography>
            <CareFormFields
              category={category}
              state={state}
              errors={errors}
              onChange={(patch) => setState((current) => ({ ...current, ...patch }))}
              now={now}
              testId="care-batch"
            />
          </>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        {found !== null && (
          <Button onClick={() => setFound(null)} disabled={busy} sx={{ minHeight: 48 }}>
            {t('pages.bed.care.batch.back')}
          </Button>
        )}
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        {found === null ? (
          <Button
            variant="contained"
            onClick={() => void find()}
            disabled={selected.size === 0}
            loading={busy}
            sx={{ minHeight: 48 }}
            data-testid="care-batch-find"
          >
            {t('pages.bed.care.batch.find')}
          </Button>
        ) : (
          found.tasks.length > 0 && (
            <Button
              variant="contained"
              onClick={() => void submit()}
              loading={busy}
              sx={{ minHeight: 48 }}
              data-testid="care-batch-submit"
            >
              {t('pages.bed.care.batch.submit', { count })}
            </Button>
          )
        )}
      </DialogActions>
    </Dialog>
  );
}
