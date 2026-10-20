/**
 * "Save as template" (REQ-053 GP-FR-044, WP 7.10): the selected bed becomes a template of the tenant - its
 * shape in the bed frame, its bed type and its height. Nothing of the bed's content (plants, tasks, notes) goes
 * along, and the soil values and spacing stay `null` (E-10: no value without a source). Its own lazy chunk.
 */
import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

const PREFIX = 'pages.gardenPlan.editor.templates.save';

interface SaveAsTemplateDialogProps {
  open: boolean;
  defaultName: string;
  /** Resolves with the message code of a refusal, or `null` when the template was saved. */
  onSave: (name: string) => Promise<string | null>;
  onClose: () => void;
}

function Form({ defaultName, onSave, onClose }: Omit<SaveAsTemplateDialogProps, 'open'>) {
  const { t } = useTranslation();
  const [name, setName] = useState(defaultName);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (name.trim() === '' || busy) return;
    setBusy(true);
    const refusal = await onSave(name.trim());
    setBusy(false);
    if (refusal) setError(refusal);
  };
  return (
    <form onSubmit={(event) => void submit(event)} noValidate>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t(`${PREFIX}.intro`)}
        </Typography>
        <TextField
          autoFocus
          fullWidth
          size="small"
          label={t(`${PREFIX}.name`)}
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            setError(null);
          }}
          required
          error={name.trim() === ''}
          slotProps={{
            htmlInput: { maxLength: 200, 'data-testid': 'garden-plan-template-save-name' },
          }}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
        />
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="garden-plan-template-save-error">
            {t(`${PREFIX}.error.${error}`, { defaultValue: t(`${PREFIX}.error.generic`) })}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }} data-testid="garden-plan-template-save-cancel">
          {t('pages.gardenPlan.editor.draw.cancel')}
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={busy || name.trim() === ''}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-template-save-submit"
        >
          {t(`${PREFIX}.submit`)}
        </Button>
      </DialogActions>
    </form>
  );
}

export default function SaveAsTemplateDialog(props: SaveAsTemplateDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { open, ...rest } = props;
  return (
    <Dialog
      open={open}
      onClose={props.onClose}
      fullScreen={fullScreen}
      maxWidth="xs"
      fullWidth
      aria-labelledby="garden-plan-template-save-title"
      data-testid="garden-plan-template-save-dialog"
    >
      <DialogTitle id="garden-plan-template-save-title">{t(`${PREFIX}.title`)}</DialogTitle>
      {open && <Form {...rest} />}
    </Dialog>
  );
}
