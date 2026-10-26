/**
 * Create a care task on the bed (REQ-053 GP-FR-080/081): "for the bed" binds the task to the bed;
 * "for every plant" creates one task per plant standing there, in one request (no bed task, #2462). The category list follows the bed (F-03).
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import MenuItem from '@mui/material/MenuItem';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { categoriesFor, type CareContext } from './careCategories';
import { createBedTask, createTasksForEachPlant } from './careApi';
import type { TaskScope } from './careTypes';

const NAME_MAX = 200;

interface CareTaskDialogProps {
  bedKey: string;
  context: CareContext;
  plantCount: number;
  onClose: () => void;
  /** The task (or the per-plant tasks) exist; `count` is how many tasks were created. */
  onCreated: (count: number, scope: TaskScope) => void;
}

export default function CareTaskDialog({ bedKey, context, plantCount, onClose, onCreated }: CareTaskDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const categories = useMemo(() => categoriesFor(context, 'task'), [context]);
  const [category, setCategory] = useState<string>(categories[0] ?? 'maintenance');
  const [name, setName] = useState('');
  const [due, setDue] = useState('');
  const [scope, setScope] = useState<TaskScope>('bed');
  const [saving, setSaving] = useState(false);

  const effectiveName = name.trim() !== '' ? name.trim() : t(`enums.taskCategory.${category}`);

  const submit = async () => {
    setSaving(true);
    try {
      const body = {
        name: effectiveName.slice(0, NAME_MAX),
        category,
        entity_type: 'location' as const,
        entity_key: bedKey,
        // A due day is due until its end: it is overdue the next morning, not at noon.
        ...(due !== '' ? { due_date: new Date(`${due}T23:59:00`).toISOString() } : {}),
      };
      if (scope === 'plants') {
        const created = await createTasksForEachPlant(body);
        if (created.length > 0) {
          onCreated(created.length, 'plants');
          return;
        }
        // No plant stands in the bed (or its sub-locations) after all: the server created nothing, so the
        // task goes on the bed instead of being lost.
      }
      await createBedTask(body);
      onCreated(1, 'bed');
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="care-task-title"
      data-testid="care-task-dialog"
    >
      <DialogTitle id="care-task-title">{t('pages.bed.care.create.title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <TextField
          select
          autoFocus
          label={t('pages.bed.care.create.category')}
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          slotProps={{ htmlInput: { 'data-testid': 'care-task-category' } }}
        >
          {categories.map((value) => (
            <MenuItem key={value} value={value}>
              {t(`enums.taskCategory.${value}`)}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label={t('pages.bed.care.create.name')}
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder={t(`enums.taskCategory.${category}`)}
          helperText={t('pages.bed.care.create.nameHint')}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          slotProps={{ htmlInput: { maxLength: NAME_MAX, 'data-testid': 'care-task-name' } }}
        />
        <TextField
          type="date"
          label={t('pages.bed.care.create.due')}
          value={due}
          onChange={(event) => setDue(event.target.value)}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { 'data-testid': 'care-task-due' } }}
        />
        <FormControl>
          <FormLabel id="care-task-scope-label">{t('pages.bed.care.create.scope')}</FormLabel>
          <RadioGroup
            aria-labelledby="care-task-scope-label"
            value={scope}
            onChange={(event) => setScope(event.target.value as TaskScope)}
          >
            <FormControlLabel
              value="bed"
              control={<Radio />}
              label={t('pages.bed.care.create.scopeBed')}
              sx={{ minHeight: 44 }}
              data-testid="care-task-scope-bed"
            />
            <FormControlLabel
              value="plants"
              control={<Radio />}
              label={t('pages.bed.care.create.scopePlants')}
              disabled={plantCount === 0}
              sx={{ minHeight: 44 }}
              data-testid="care-task-scope-plants"
            />
          </RadioGroup>
          <FormHelperText>
            {plantCount === 0
              ? t('pages.bed.care.create.scopeNoPlants')
              : t('pages.bed.care.create.scopePlantsHint', { count: plantCount })}
          </FormHelperText>
        </FormControl>
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2, flexWrap: 'wrap', rowGap: 1 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          loading={saving}
          sx={{ minHeight: 48 }}
          data-testid="care-task-submit"
        >
          {t('pages.bed.care.create.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
