/**
 * The "Care" tab of the bed view (REQ-053 GP-FR-083…086, GP-FR-090): the open and overdue tasks of
 * the bed and of the plants standing in it, completion with the short category dialog, tasks "for the
 * bed" or "for every plant", care logged without a task, and the system's suggestions in their own
 * section. Every write offers an undo for eight seconds.
 */
import { useCallback, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import AddTaskIcon from '@mui/icons-material/AddTask';
import EditNoteIcon from '@mui/icons-material/EditNote';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { BedSummary } from '../bed/types';
import { completeBedTask, reopenBedTask, reopenWithUndo, skipBedTask, voidCareEvent } from './careApi';
import { type CareContext } from './careCategories';
import type { CareEventRef, CareTask, CompletionPayload, TaskScope } from './careTypes';
import CareCompletionDialog from './CareCompletionDialog';
import CareLogDialog from './CareLogDialog';
import { isOverdue } from '../model/overdue';
import CareTaskDialog from './CareTaskDialog';
import CareTaskList from './CareTaskList';
import { isDuplicateTap } from './submitGuard';
import { useBedCare } from './useBedCare';
import { useUndoSnackbar } from './useUndoSnackbar';

interface BedCareTabProps {
  bed: BedSummary;
  /** The bed's own data changed (counters, last care); the page reloads its summary. */
  onChanged: () => void;
}

export function isTaskOverdue(task: CareTask, now: number): boolean {
  return isOverdue(task.due_date, new Date(now));
}

export default function BedCareTab({ bed, onChanged }: BedCareTabProps) {
  const { t, i18n } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const { handleError } = useApiError();
  const notification = useNotification();
  const { offerUndo } = useUndoSnackbar();
  const care = useBedCare(bed.key);
  const [completing, setCompleting] = useState<CareTask | null>(null);
  const [saving, setSaving] = useState(false);
  const [creating, setCreating] = useState(false);
  const [logging, setLogging] = useState(false);
  const lastSubmitAt = useRef(0);
  const savingRef = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  /** The row that opened a dialog may be gone after the reload; keep keyboard and screen-reader users in the tab. */
  const restoreFocus = () => {
    window.setTimeout(() => {
      const active = document.activeElement;
      if (!active || active === document.body) rootRef.current?.focus();
    }, 0);
  };

  const context = useMemo<CareContext>(
    () => ({ growingMedium: bed.soil_profile?.growing_medium_kind ?? null, locationTypeKey: bed.location_type_key }),
    [bed.soil_profile?.growing_medium_kind, bed.location_type_key],
  );
  const { reload } = care;
  const changed = useCallback(() => {
    reload();
    onChanged();
  }, [reload, onChanged]);

  const ready = care.state.status === 'ready' ? care.state : null;
  const sections = useMemo(() => {
    // "Overdue" is judged at the instant the list was loaded, so a re-render never moves a task between sections.
    const now = ready?.loadedAt ?? 0;
    const tasks = ready?.tasks ?? [];
    return {
      overdue: tasks.filter((task) => !task.suggested && isTaskOverdue(task, now)),
      open: tasks.filter((task) => !task.suggested && !isTaskOverdue(task, now)),
      suggested: tasks.filter((task) => task.suggested),
    };
  }, [ready]);
  const taskName = (task: CareTask) => (i18n.language.startsWith('de') && task.name_de) || task.name;

  const complete = async (task: CareTask, payload: CompletionPayload) => {
    const now = Date.now();
    // A double tap is one tap; the dialog also stays locked until the answer arrives.
    if (isDuplicateTap(lastSubmitAt.current, now, savingRef.current)) return;
    lastSubmitAt.current = now;
    savingRef.current = true;
    setSaving(true);
    try {
      await completeBedTask(task.key, payload);
      setCompleting(null);
      changed();
      restoreFocus();
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
      savingRef.current = false;
      setSaving(false);
    }
  };

  const dismiss = async (task: CareTask) => {
    if (saving) return;
    setSaving(true);
    try {
      await skipBedTask(task.key);
      changed();
      restoreFocus();
      offerUndo({
        message: t('pages.bed.care.undo.dismissed', { name: taskName(task) }),
        undo: async () => {
          await reopenBedTask(task.key);
        },
        onUndone: changed,
      });
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  const onLogged = (event: CareEventRef, label: string) => {
    setLogging(false);
    onChanged();
    restoreFocus();
    offerUndo({
      message: t('pages.bed.care.undo.logged', { category: label }),
      undo: () => voidCareEvent(event.key),
      onUndone: onChanged,
    });
  };

  const onCreated = (count: number, scope: TaskScope) => {
    setCreating(false);
    changed();
    restoreFocus();
    if (scope === 'bedOnly') return; // the error toast of the failed fan-out is already up
    notification.success(
      scope === 'plants' ? t('pages.bed.care.create.createdPlants', { count }) : t('pages.bed.care.create.createdBed'),
    );
  };

  const total = sections.overdue.length + sections.open.length + sections.suggested.length;

  return (
    <Box
      ref={rootRef}
      tabIndex={-1}
      data-testid="bed-care-tab"
      sx={{ display: 'flex', flexDirection: 'column', gap: 3, outline: 'none' }}
    >
      {canEdit && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<AddTaskIcon />}
            onClick={() => setCreating(true)}
            sx={{ minHeight: 48, flex: { xs: '1 1 100%', sm: '0 0 auto' } }}
            data-testid="care-create"
          >
            {t('pages.bed.care.create.open')}
          </Button>
          <Button
            variant="outlined"
            startIcon={<EditNoteIcon />}
            onClick={() => setLogging(true)}
            sx={{ minHeight: 48, flex: { xs: '1 1 100%', sm: '0 0 auto' } }}
            data-testid="care-log"
          >
            {t('pages.bed.care.log.open')}
          </Button>
        </Box>
      )}

      {care.state.status === 'loading' && (
        <Box role="status" aria-busy="true" aria-label={t('pages.bed.care.loading')}>
          <LoadingSkeleton variant="card" />
        </Box>
      )}
      {care.state.status === 'error' && <ErrorDisplay error={care.state.message} onRetry={reload} />}
      {ready && total === 0 && (
        <EmptyState
          message={t('pages.bed.care.empty.title')}
          description={t(canEdit ? 'pages.bed.care.empty.descriptionEdit' : 'pages.bed.care.empty.description')}
        />
      )}
      {ready &&
        (['overdue', 'open', 'suggested'] as const).map((kind) =>
          sections[kind].length > 0 ? (
            <CareTaskList
              key={kind}
              kind={kind}
              tasks={sections[kind]}
              plants={ready.plants ?? []}
              canEdit={canEdit}
              busy={saving}
              onComplete={setCompleting}
              onDismiss={(task) => void dismiss(task)}
            />
          ) : null,
        )}

      {completing && (
        <CareCompletionDialog
          category={completing.category}
          subject={taskName(completing)}
          saving={saving}
          onSubmit={(payload) => void complete(completing, payload)}
          onClose={() => setCompleting(null)}
        />
      )}
      {creating && (
        <CareTaskDialog
          bedKey={bed.key}
          context={context}
          plantCount={ready?.plants?.length ?? bed.active_plant_count}
          onClose={() => setCreating(false)}
          onCreated={onCreated}
        />
      )}
      {logging && (
        <CareLogDialog bedKey={bed.key} context={context} onClose={() => setLogging(false)} onLogged={onLogged} />
      )}
    </Box>
  );
}
