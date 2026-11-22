/**
 * The "Suggestions" section of the bed care tab (REQ-053 GP-FR-086, GP-API-040): tasks the system proposes
 * (`suggested = true`), each with its reason and the two decisions "Accept" (it becomes an ordinary open task) and
 * "Dismiss" (it is closed without a care entry). The section renders nothing when there is no suggestion.
 *
 * No producer writes suggestions yet (REQ-053 E-02: that belongs to the ADR-008 propagation strand), so in a
 * running installation the section stays hidden until one exists.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import { formatBedDate } from '../bed/bedFormat';
import { taskTarget } from './careCategories';
import type { BedPlantRef, CareTask } from './careTypes';

interface SuggestionListProps {
  tasks: readonly CareTask[];
  plants: readonly BedPlantRef[];
  canEdit: boolean;
  /** A write is running; the decisions wait for its answer. */
  busy: boolean;
  onAccept: (task: CareTask) => void;
  onDismiss: (task: CareTask) => void;
}

const HEADING_ID = 'care-section-suggested-heading';

export default function SuggestionList({ tasks, plants, canEdit, busy, onAccept, onDismiss }: SuggestionListProps) {
  const { t, i18n } = useTranslation();
  if (tasks.length === 0) return null;
  const language = i18n.language;
  const taskName = (task: CareTask) => (language.startsWith('de') && task.name_de) || task.name;
  const plantName = (task: CareTask): string | null =>
    plants.find((plant) => plant.plantKey === task.entity_key)?.instanceId ?? null;

  return (
    <Box component="section" aria-labelledby={HEADING_ID} data-testid="care-section-suggested">
      <Typography id={HEADING_ID} variant="h6" component="h2" sx={{ mb: 1 }}>
        {t('pages.bed.care.sections.suggested', { count: tasks.length })}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('pages.bed.care.sections.suggestedHint')}
      </Typography>
      <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {tasks.map((task) => {
          const target = taskTarget(task);
          const due = formatBedDate(task.due_date, language);
          const name = taskName(task);
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
                borderStyle: 'dashed',
                borderColor: 'divider',
                borderRadius: 1,
                bgcolor: 'background.paper',
              }}
            >
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography variant="subtitle1" sx={{ overflowWrap: 'anywhere' }}>
                  {name}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 0.5, overflowWrap: 'anywhere' }}
                  data-testid={`care-reason-${task.key}`}
                >
                  {task.suggestion_reason
                    ? t('pages.bed.care.suggestions.reason', { reason: task.suggestion_reason })
                    : t('pages.bed.care.sections.suggestedNoReason')}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5, alignItems: 'center' }}>
                  <Chip size="small" label={t(`enums.taskCategory.${task.category}`, { defaultValue: task.category })} />
                  <Chip
                    size="small"
                    variant="outlined"
                    label={
                      target === 'plant'
                        ? t('pages.bed.care.target.plant', {
                            name: plantName(task) ?? t('pages.bed.care.target.plantUnknown'),
                          })
                        : target === 'bed'
                          ? t('pages.bed.care.target.bed')
                          : t('pages.bed.care.target.other')
                    }
                  />
                  {due && (
                    <Typography component="span" variant="body2" color="text.secondary">
                      {t('pages.bed.care.due', { date: due })}
                    </Typography>
                  )}
                </Box>
              </Box>
              {canEdit && (
                <Box sx={{ display: 'flex', gap: 1, flexShrink: 0, width: { xs: '100%', sm: 'auto' } }}>
                  <Button
                    variant="outlined"
                    color="inherit"
                    onClick={() => onDismiss(task)}
                    disabled={busy}
                    sx={{ minHeight: 48, flex: { xs: 1, sm: 'none' } }}
                    data-testid={`care-dismiss-${task.key}`}
                    aria-label={t('pages.bed.care.dismissFor', { name })}
                  >
                    {t('pages.bed.care.dismiss')}
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => onAccept(task)}
                    disabled={busy}
                    sx={{ minHeight: 48, minWidth: 96, flex: { xs: 1, sm: 'none' } }}
                    data-testid={`care-accept-${task.key}`}
                    aria-label={t('pages.bed.care.suggestions.acceptFor', { name })}
                  >
                    {t('pages.bed.care.suggestions.accept')}
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
