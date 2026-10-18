/**
 * One section of the care tab (REQ-053 GP-FR-083/086): a heading with the count and the task rows.
 * A row names the task, what it hangs off (the bed or a plant) and when it is due; "Done" opens the
 * short completion dialog. In the suggestions section a row carries the reason and the two actions
 * "do now" and "dismiss" instead.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import { formatBedDate } from '../bed/bedFormat';
import { taskTarget } from './careCategories';
import type { BedPlantRef, CareTask } from './careTypes';

export type SectionKind = 'overdue' | 'open' | 'suggested';

interface CareTaskListProps {
  kind: SectionKind;
  tasks: readonly CareTask[];
  plants: readonly BedPlantRef[];
  canEdit: boolean;
  /** A write is running; the actions wait for its answer. */
  busy: boolean;
  onComplete: (task: CareTask) => void;
  onDismiss: (task: CareTask) => void;
}

export default function CareTaskList({ kind, tasks, plants, canEdit, busy, onComplete, onDismiss }: CareTaskListProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const headingId = `care-section-${kind}`;
  const plantName = (task: CareTask): string | null =>
    plants.find((plant) => plant.plantKey === task.entity_key)?.instanceId ?? null;
  const taskName = (task: CareTask) => (language.startsWith('de') && task.name_de) || task.name;

  return (
    <Box component="section" aria-labelledby={headingId} data-testid={`care-section-${kind}`}>
      <Typography
        id={headingId}
        variant="h6"
        component="h2"
        color={kind === 'overdue' ? 'error' : 'text.primary'}
        sx={{ mb: 1 }}
      >
        {t(`pages.bed.care.sections.${kind}`, { count: tasks.length })}
      </Typography>
      {kind === 'suggested' && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.bed.care.sections.suggestedHint')}
        </Typography>
      )}
      <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {tasks.map((task) => {
          const target = taskTarget(task);
          const due = formatBedDate(task.due_date, language);
          const name = target === 'plant' ? plantName(task) : null;
          return (
            <Box
              component="li"
              key={task.key}
              data-testid={`care-task-${task.key}`}
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                alignItems: { sm: 'center' },
                gap: 1,
                p: 1.5,
                border: 1,
                borderColor: kind === 'overdue' ? 'error.main' : 'divider',
                borderRadius: 1,
                bgcolor: 'background.paper',
              }}
            >
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography variant="subtitle1" sx={{ overflowWrap: 'anywhere' }}>
                  {taskName(task)}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5, alignItems: 'center' }}>
                  <Chip size="small" label={t(`enums.taskCategory.${task.category}`, { defaultValue: task.category })} />
                  <Chip
                    size="small"
                    variant="outlined"
                    label={
                      target === 'plant'
                        ? t('pages.bed.care.target.plant', { name: name ?? t('pages.bed.care.target.plantUnknown') })
                        : target === 'bed'
                          ? t('pages.bed.care.target.bed')
                          : t('pages.bed.care.target.other')
                    }
                  />
                  {due && (
                    <Typography
                      component="span"
                      variant="body2"
                      color={kind === 'overdue' ? 'error' : 'text.secondary'}
                      data-testid={`care-task-due-${task.key}`}
                    >
                      {kind === 'overdue'
                        ? t('pages.bed.care.dueOverdue', { date: due })
                        : t('pages.bed.care.due', { date: due })}
                    </Typography>
                  )}
                </Box>
                {kind === 'suggested' && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }} data-testid={`care-reason-${task.key}`}>
                    {task.suggestion_reason ?? t('pages.bed.care.sections.suggestedNoReason')}
                  </Typography>
                )}
              </Box>
              {canEdit && (
                <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
                  {kind === 'suggested' && (
                    <Button
                      variant="outlined"
                      color="inherit"
                      onClick={() => onDismiss(task)}
                      disabled={busy}
                      sx={{ minHeight: 48 }}
                      data-testid={`care-dismiss-${task.key}`}
                      aria-label={t('pages.bed.care.dismissFor', { name: taskName(task) })}
                    >
                      {t('pages.bed.care.dismiss')}
                    </Button>
                  )}
                  <Button
                    variant="contained"
                    onClick={() => onComplete(task)}
                    disabled={busy}
                    sx={{ minHeight: 48, minWidth: 96 }}
                    data-testid={`care-done-${task.key}`}
                    aria-label={t(kind === 'suggested' ? 'pages.bed.care.doNowFor' : 'pages.bed.care.doneFor', { name: taskName(task) })}
                  >
                    {kind === 'suggested' ? t('pages.bed.care.doNow') : t('pages.bed.care.done')}
                  </Button>
                </Box>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
