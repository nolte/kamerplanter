/**
 * The text of a new caption (REQ-053 GP-UX-071, #2913): the tool "Text" set its anchor on the plan, this small dialog
 * asks for the one line it reads. The rules are the server's (`textLabelProblem`): not empty, at most
 * `TEXT_LABEL_MAX_CHARS` characters, no line break or control character - checked here, so a refusal is a sentence
 * under the field and never a failed save. Enter confirms, Esc and "Cancel" leave without a caption.
 *
 * The editor turns the text into the caption (one `create_garden_object`, one undo step); a placement the plan refuses
 * (outside the boundary) comes back as `error` and keeps the dialog open with the text typed.
 */
import { useId, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { TEXT_LABEL_MAX_CHARS, textLabelProblem, textLength } from '../model/textLabel';

const PREFIX = 'pages.gardenPlan.editor';

interface TextLabelDialogProps {
  open: boolean;
  /** A plan rule refused the caption where it was set (`geometry.outside_parent`, ...); `null` = none. */
  error: string | null;
  onSubmit: (text: string) => void;
  onClose: () => void;
}

interface TextFormProps {
  error: string | null;
  titleId: string;
  onSubmit: (text: string) => void;
  onClose: () => void;
}

function TextForm({ error, titleId, onSubmit, onClose }: TextFormProps) {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  // The rule is told once the user tried to confirm - an empty field is no mistake while it is being filled.
  const [tried, setTried] = useState(false);
  const problem = textLabelProblem(text);
  const shownProblem = tried || problem === 'too_long' || problem === 'control' ? problem : null;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTried(true);
    if (problem !== null) return;
    onSubmit(text.trim());
  };

  return (
    <Box component="form" noValidate onSubmit={submit} aria-labelledby={titleId}>
      <DialogContent sx={{ pt: 1 }}>
        <TextField
          autoFocus
          fullWidth
          size="small"
          label={t(`${PREFIX}.text.field`)}
          value={text}
          onChange={(event) => setText(event.target.value)}
          error={shownProblem !== null}
          helperText={
            shownProblem !== null
              ? t(`${PREFIX}.text.problem.${shownProblem}`, { max: TEXT_LABEL_MAX_CHARS })
              : t(`${PREFIX}.text.counter`, { count: textLength(text.trim()), max: TEXT_LABEL_MAX_CHARS })
          }
          slotProps={{
            htmlInput: { 'data-testid': 'garden-plan-text-input', autoComplete: 'off', spellCheck: true },
            formHelperText: (shownProblem !== null ? { role: 'alert' } : {}) as Record<string, string>,
          }}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
        />
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="garden-plan-text-error">
            {t(`${PREFIX}.notice.${error}`, { defaultValue: t(`${PREFIX}.notice.generic`) })}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }} data-testid="garden-plan-text-cancel">
          {t(`${PREFIX}.draw.cancel`)}
        </Button>
        <Button variant="contained" type="submit" sx={{ minHeight: 48 }} data-testid="garden-plan-text-submit">
          {t(`${PREFIX}.text.submit`)}
        </Button>
      </DialogActions>
    </Box>
  );
}

export function TextLabelDialog({ open, error, onSubmit, onClose }: TextLabelDialogProps) {
  const { t } = useTranslation();
  const titleId = useId();
  const theme = useTheme();
  // Below sm the dialog is full screen, so the keyboard and the field do not fight for a small card.
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      aria-labelledby={titleId}
      data-testid="garden-plan-text-dialog"
    >
      <DialogTitle id={titleId}>{t(`${PREFIX}.text.title`)}</DialogTitle>
      {/* Mounted only while open: every caption starts from an empty field. */}
      {open && <TextForm error={error} titleId={titleId} onSubmit={onSubmit} onClose={onClose} />}
    </Dialog>
  );
}
