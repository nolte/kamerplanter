/**
 * The short completion dialog (REQ-053 GP-FR-084/085/088): asks only the fields of the task's
 * category, all optional, and hands the payload to the caller. "Done" without any input is valid.
 * Used for one task and, with a count, for several tasks of the same category on several beds.
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { formKindOf } from './careCategories';
import { buildCompletionPayload, defaultUnit, emptyForm, validateForm, type CareFormState } from './careForm';
import CareFormFields from './CareFormFields';
import type { CompletionPayload } from './careTypes';

interface CareCompletionDialogProps {
  category: string;
  /** What is being completed: a task name, or "3 tasks on 3 beds". */
  subject: string;
  saving: boolean;
  onSubmit: (payload: CompletionPayload) => void;
  onClose: () => void;
}

export default function CareCompletionDialog({
  category,
  subject,
  saving,
  onSubmit,
  onClose,
}: CareCompletionDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const now = useMemo(() => new Date(), []);
  const [state, setState] = useState<CareFormState>(() => ({
    ...emptyForm(now),
    unit: defaultUnit(formKindOf(category)),
  }));
  const [showErrors, setShowErrors] = useState(false);
  const errors = showErrors ? validateForm(state, new Date()) : {};

  const submit = () => {
    const found = validateForm(state, new Date());
    if (Object.keys(found).length > 0) {
      setShowErrors(true);
      return;
    }
    onSubmit(buildCompletionPayload(state, category));
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="care-complete-title"
      data-testid="care-complete-dialog"
    >
      <DialogTitle id="care-complete-title">
        {t('pages.bed.care.complete.title', { category: t(`enums.taskCategory.${category}`) })}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary" data-testid="care-complete-subject">
          {subject}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('pages.bed.care.complete.optionalHint')}
        </Typography>
        <CareFormFields
          category={category}
          state={state}
          errors={errors}
          onChange={(patch) => setState((current) => ({ ...current, ...patch }))}
          now={now}
          testId="care-complete"
        />
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2, flexWrap: 'wrap', rowGap: 1 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={submit}
          loading={saving}
          sx={{ minHeight: 48 }}
          data-testid="care-complete-submit"
        >
          {t('pages.bed.care.complete.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
