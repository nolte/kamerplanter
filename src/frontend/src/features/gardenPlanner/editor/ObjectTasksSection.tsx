/**
 * "Aufgaben" in the properties panel of a compost, water source or storage object (REQ-053 R-7.2, W-008, Anhang A
 * 62, WP 10.10): the object's open tasks and "Aufgabe anlegen", which opens the bed's task dialog with the object as
 * its target (`entity_type = garden_object`). No other class gets the section: the server refuses a task on it (422).
 *
 * Online-only like every server write of the editor (G-W9): without a connection the action is locked with a hint,
 * not an error, and the list is not read. An object drawn but not saved yet has no key the server knows; it says so.
 */
import { lazy, Suspense, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import AddTaskIcon from '@mui/icons-material/AddTask';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { formatBedDate } from '../bed/bedFormat';
import { objectTakesTasks } from '../care/careCategories';
import { useObjectTasks } from '../care/useObjectTasks';
import { isTempKey } from '../model/planModel';
import { isOverdue } from '../model/overdue';

// The dialog loads when it is opened, not with the editor (E-12 budget).
const CareTaskDialog = lazy(() => import('../care/CareTaskDialog'));

const PREFIX = 'pages.gardenPlan.editor.panel.objectTasks';

interface ObjectTasksSectionProps {
  objectKey: string;
  /** `object_type` of the garden object; the section renders only for `compost`, `water_source`, `storage`. */
  objectType: string;
  /** What the dialog title names: the object's label, or its class without one. */
  objectName: string;
}

export default function ObjectTasksSection({ objectKey, objectType, objectName }: ObjectTasksSectionProps) {
  const { t, i18n } = useTranslation();
  const online = useOnlineStatus();
  const { canEdit } = useTenantPermissions();
  const notification = useNotification();
  const [creating, setCreating] = useState(false);
  const unsaved = isTempKey(objectKey);
  const takesTasks = objectTakesTasks(objectType);
  const { state, reload } = useObjectTasks(objectKey, takesTasks && online && !unsaved);
  const target = useMemo(() => ({ key: objectKey, name: objectName }), [objectKey, objectName]);

  if (!takesTasks) return null;

  const locked = !online || unsaved;
  const taskName = (name: string, nameDe?: string | null) => (i18n.language.startsWith('de') && nameDe) || name;

  let body: ReactNode;
  if (unsaved) {
    body = (
      <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-object-tasks-unsaved">
        {t(`${PREFIX}.unsaved`)}
      </Typography>
    );
  } else if (!online) {
    body = (
      <Alert severity="info" role="status" data-testid="garden-plan-panel-object-tasks-offline">
        {t(`${PREFIX}.offline`)}
      </Alert>
    );
  } else if (state.status === 'loading' || state.status === 'idle') {
    body = (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} role="status">
        <CircularProgress size={16} />
        <Typography variant="body2">{t(`${PREFIX}.loading`)}</Typography>
      </Box>
    );
  } else if (state.status === 'error') {
    body = (
      <Alert
        severity="warning"
        data-testid="garden-plan-panel-object-tasks-error"
        action={
          <Button color="inherit" onClick={reload} sx={{ minHeight: 48 }}>
            {t(`${PREFIX}.retry`)}
          </Button>
        }
      >
        {t(`${PREFIX}.error`, { message: state.message })}
      </Alert>
    );
  } else if (state.tasks.length === 0) {
    body = (
      <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-object-tasks-empty">
        {t(`${PREFIX}.empty`)}
      </Typography>
    );
  } else {
    const now = new Date(state.loadedAt);
    body = (
      <Box
        component="ul"
        data-testid="garden-plan-panel-object-tasks-list"
        sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}
      >
        {state.tasks.map((task) => {
          const overdue = isOverdue(task.due_date, now);
          const due = formatBedDate(task.due_date, i18n.language);
          return (
            <Box
              component="li"
              key={task.key}
              data-testid={`garden-plan-panel-object-task-${task.key}`}
              data-overdue={overdue ? 'true' : 'false'}
              sx={{
                p: 1,
                border: 1,
                borderColor: overdue ? 'error.main' : 'divider',
                borderRadius: 1,
                minWidth: 0,
              }}
            >
              <Typography variant="body2" sx={{ overflowWrap: 'anywhere', fontWeight: 500 }}>
                {taskName(task.name, task.name_de)}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                <Chip size="small" label={t(`enums.taskCategory.${task.category}`, { defaultValue: task.category })} />
                {due && (
                  <Typography variant="body2" component="span" color={overdue ? 'error' : 'text.secondary'}>
                    {overdue ? t(`${PREFIX}.dueOverdue`, { date: due }) : t(`${PREFIX}.due`, { date: due })}
                  </Typography>
                )}
              </Box>
            </Box>
          );
        })}
      </Box>
    );
  }

  return (
    <Box
      component="section"
      aria-labelledby="garden-plan-panel-object-tasks-title"
      data-testid="garden-plan-panel-object-tasks"
      data-object-type={objectType}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
    >
      <Typography variant="subtitle2" component="h4" id="garden-plan-panel-object-tasks-title">
        {t(`${PREFIX}.title`)}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t(`${PREFIX}.help`)}
      </Typography>
      {body}
      {canEdit && (
        <Button
          variant="outlined"
          startIcon={<AddTaskIcon />}
          disabled={locked}
          onClick={() => setCreating(true)}
          sx={{ minHeight: 48, alignSelf: 'flex-start' }}
          data-testid="garden-plan-panel-object-task-add"
        >
          {t(`${PREFIX}.add`)}
        </Button>
      )}
      {creating && (
        <Suspense fallback={null}>
          <CareTaskDialog
            gardenObject={target}
            onClose={() => setCreating(false)}
            onCreated={() => {
              setCreating(false);
              reload();
              notification.success(t(`${PREFIX}.created`, { name: objectName }));
            }}
          />
        </Suspense>
      )}
    </Box>
  );
}
