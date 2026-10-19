/**
 * Log care without a task (REQ-053 GP-FR-090): "I just mulched". The category list follows the bed
 * (F-03); the form below is the same short form as for a completion. The line is a care event with
 * `trigger = manual`; the author can take it back for ten minutes (the undo snackbar).
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { categoriesFor, formKindOf, NOTE_CATEGORY, type CareContext } from './careCategories';
import { careCategoryLabel } from './careLabels';
import { buildLogBody, defaultUnit, emptyForm, validateForm, type CareFormState } from './careForm';
import { logCareEvent } from './careApi';
import CareFormFields from './CareFormFields';
import type { CareEventRef } from './careTypes';

interface CareLogDialogProps {
  bedKey: string;
  context: CareContext;
  onClose: () => void;
  /** The line was stored; `label` is its category's name for the confirmation. */
  onLogged: (event: CareEventRef, label: string) => void;
  /**
   * Log exactly this category, without the category list: the field-mode chips "harvested" and "note"
   * (GP-UX-029) open the short form of their category directly.
   */
  fixedCategory?: string;
  /** Edge of the action buttons in px; field mode passes the kiosk target (64 px, GP-UX-020). */
  touchTarget?: number;
}

export default function CareLogDialog({
  bedKey,
  context,
  onClose,
  onLogged,
  fixedCategory,
  touchTarget = 48,
}: CareLogDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const now = useMemo(() => new Date(), []);
  const categories = useMemo(
    () => (fixedCategory ? [fixedCategory] : categoriesFor(context, 'log')),
    [context, fixedCategory],
  );
  const [category, setCategory] = useState<string>(categories[0] ?? NOTE_CATEGORY);
  const [state, setState] = useState<CareFormState>(() => ({
    ...emptyForm(now),
    unit: defaultUnit(formKindOf(categories[0] ?? NOTE_CATEGORY)),
  }));
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  const errors = showErrors ? validateForm(state, new Date()) : {};
  const label = (value: string) => careCategoryLabel(t, value);

  const changeCategory = (next: string) => {
    setCategory(next);
    // The quantity, unit, material and product belong to the old category; the note and the instant stay.
    setState((current) => ({
      ...emptyForm(now),
      performedAt: current.performedAt,
      performedAtTouched: current.performedAtTouched,
      note: current.note,
      unit: defaultUnit(formKindOf(next)),
    }));
  };

  const submit = async () => {
    const instant = new Date();
    if (Object.keys(validateForm(state, instant)).length > 0) {
      setShowErrors(true);
      return;
    }
    setSaving(true);
    try {
      const event = await logCareEvent(buildLogBody(state, category, bedKey, label(category), instant));
      onLogged(event, label(category));
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
      aria-labelledby="care-log-title"
      data-testid="care-log-dialog"
    >
      <DialogTitle id="care-log-title">
        {fixedCategory ? label(fixedCategory) : t('pages.bed.care.log.title')}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        {!fixedCategory && (
          <TextField
            select
            autoFocus
            label={t('pages.bed.care.log.category')}
            value={category}
            onChange={(event) => changeCategory(event.target.value)}
            helperText={t('pages.bed.care.log.categoryHint')}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            slotProps={{ htmlInput: { 'data-testid': 'care-log-category' } }}
          >
            {categories.map((value) => (
              <MenuItem key={value} value={value}>
                {label(value)}
              </MenuItem>
            ))}
          </TextField>
        )}
        <CareFormFields
          category={category}
          state={state}
          errors={errors}
          onChange={(patch) => setState((current) => ({ ...current, ...patch }))}
          now={now}
          testId="care-log"
          noteLabelKey={category === NOTE_CATEGORY ? 'pages.bed.care.log.noteText' : 'pages.bed.care.form.note'}
        />
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2, flexWrap: 'wrap', rowGap: 1 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: touchTarget }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          loading={saving}
          sx={{ minHeight: touchTarget, minWidth: touchTarget }}
          data-testid="care-log-submit"
        >
          {t('pages.bed.care.log.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
