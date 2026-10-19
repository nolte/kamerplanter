/**
 * The tasks of the bed sheet (REQ-053 §18.1 step 4/5): overdue first, then due today, then the rest. A
 * row shows the category icon (≥ 32 px), the name, what it hangs off and when it is due; "Done" is a
 * 64 × 64 px target (UI-NFR-019 R-007, GP-ACC-029).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { formatBedDate } from '../bed/bedFormat';
import { taskTarget } from '../care/careCategories';
import { careTaskName } from '../care/careLabels';
import type { CareTask } from '../care/careTypes';
import { categoryIcon, FIELD_ICON_PX } from './fieldIcons';
import type { FieldTaskSections } from './fieldDue';

type SectionKind = keyof FieldTaskSections;
const KINDS: readonly SectionKind[] = ['overdue', 'today', 'later'];

interface FieldTaskSectionProps {
  sections: FieldTaskSections;
  /** Instance ids of the standing plants by plant key, to name the plant tasks. */
  plantNames: ReadonlyMap<string, string>;
  canEdit: boolean;
  /** "Done" is locked: a completion is waiting for its answer, or the device is offline. */
  locked: boolean;
  onDone: (task: CareTask) => void;
}

export default function FieldTaskSection({ sections, plantNames, canEdit, locked, onDone }: FieldTaskSectionProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const taskName = (task: CareTask) => careTaskName(task, language);
  const total = sections.overdue.length + sections.today.length + sections.later.length;

  return (
    <Box component="section" aria-labelledby="field-tasks-heading" data-testid="field-tasks">
      <Typography id="field-tasks-heading" variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.field.tasks.title', { count: total })}
      </Typography>
      {total === 0 && (
        <Typography variant="body1" data-testid="field-tasks-empty">
          {t('pages.gardenPlan.field.tasks.empty')}
        </Typography>
      )}
      {KINDS.map((kind) =>
        sections[kind].length === 0 ? null : (
          <Box key={kind} sx={{ mb: 2 }} data-testid={`field-tasks-${kind}`}>
            <Typography
              variant="subtitle1"
              component="h4"
              sx={{ fontWeight: 700, color: kind === 'overdue' ? 'error.main' : 'text.primary', mb: 0.5 }}
            >
              {t(`pages.gardenPlan.field.tasks.sections.${kind}`, { count: sections[kind].length })}
            </Typography>
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
              {sections[kind].map((task) => {
                const Icon = categoryIcon(task.category);
                const due = formatBedDate(task.due_date, language);
                const target = taskTarget(task);
                const plant = target === 'plant' && task.entity_key ? plantNames.get(task.entity_key) : undefined;
                return (
                  <Box
                    component="li"
                    key={task.key}
                    data-testid={`field-task-${task.key}`}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      p: 1.5,
                      border: 2,
                      borderColor: kind === 'overdue' ? 'error.main' : 'divider',
                      borderRadius: 1,
                    }}
                  >
                    <Icon sx={{ fontSize: FIELD_ICON_PX, flexShrink: 0 }} aria-hidden="true" />
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="body1" sx={{ fontWeight: 700, overflowWrap: 'anywhere' }}>
                        {taskName(task)}
                      </Typography>
                      <Typography variant="body1">
                        {t(`enums.taskCategory.${task.category}`, { defaultValue: task.category })}
                        {target === 'plant' &&
                          ` · ${t('pages.bed.care.target.plant', { name: plant ?? t('pages.bed.care.target.plantUnknown') })}`}
                      </Typography>
                      {due && (
                        <Typography
                          variant="body1"
                          sx={{ color: kind === 'overdue' ? 'error.main' : 'text.primary' }}
                          data-testid={`field-task-due-${task.key}`}
                        >
                          {kind === 'overdue'
                            ? t('pages.bed.care.dueOverdue', { date: due })
                            : t('pages.bed.care.due', { date: due })}
                        </Typography>
                      )}
                    </Box>
                    {canEdit && (
                      <Button
                        variant="contained"
                        onClick={() => onDone(task)}
                        disabled={locked}
                        sx={{
                          minWidth: KIOSK_TOUCH_TARGET,
                          minHeight: KIOSK_TOUCH_TARGET,
                          flexShrink: 0,
                          fontSize: '1rem',
                          px: 2,
                        }}
                        data-testid={`field-done-${task.key}`}
                        aria-label={t('pages.bed.care.doneFor', { name: taskName(task) })}
                      >
                        {t('pages.bed.care.done')}
                      </Button>
                    )}
                  </Box>
                );
              })}
            </Box>
          </Box>
        ),
      )}
    </Box>
  );
}
