/**
 * "Bed > From template" (REQ-053 GP-FR-044, WP 7.10): the strip under the tool bar while the template tool is
 * on. The user picks a template, turns it, then clicks (or taps) the plan where its anchor should land. Its own
 * lazy chunk: the plan route's budget does not carry the picker.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import RotateRightIcon from '@mui/icons-material/RotateRight';
import type { BedTemplates } from './useBedTemplates';
import { templateName } from './templateName';

const PREFIX = 'pages.gardenPlan.editor.templates';
const TARGET_PX = 44;

interface TemplatePanelProps {
  catalogue: BedTemplates;
  /** `null` = none picked yet. */
  templateKey: string | null;
  onTemplateKey: (key: string) => void;
  rotationDeg: number;
  onRotate: () => void;
  busy: boolean;
  /** Place the template at the middle of the view: the way without a pointer (keyboard, switch access). */
  onPlaceCenter: () => void;
  /** The ghost under the pointer sits where the template would leave the garden: the status line says so. */
  ghostInvalid?: boolean;
  onClose: () => void;
}

export default function TemplatePanel(props: TemplatePanelProps) {
  const { t } = useTranslation();
  const { catalogue, templateKey } = props;
  const known = catalogue.templates.some((template) => template.key === templateKey);
  return (
    <Box
      role="group"
      aria-label={t(`${PREFIX}.panel.label`)}
      data-testid="garden-plan-template-panel"
      onKeyDown={(event) => {
        // Esc ends the tool also when the focus is in the panel (the plan's own handler sees only its keys)
        if (event.key === 'Escape' && event.currentTarget.contains(event.target as Node)) {
          // (the open list of the select sits in a portal and closes itself first)
          event.stopPropagation();
          props.onClose();
        }
      }}
      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}
    >
      <TextField
        select
        size="small"
        label={t(`${PREFIX}.panel.pick`)}
        value={known ? templateKey : ''}
        onChange={(event) => props.onTemplateKey(event.target.value)}
        disabled={catalogue.loading}
        slotProps={{ htmlInput: { 'data-testid': 'garden-plan-template-select' } }}
        sx={{ minWidth: 240, '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
      >
        {catalogue.templates.map((template) => (
          <MenuItem key={template.key} value={template.key} sx={{ minHeight: 48 }}>
            {templateName(t, template)}
          </MenuItem>
        ))}
      </TextField>
      {catalogue.loading && (
        <CircularProgress size={20} aria-label={t(`${PREFIX}.panel.loading`)} />
      )}
      <Button
        variant="outlined"
        size="small"
        startIcon={<RotateRightIcon />}
        onClick={props.onRotate}
        data-testid="garden-plan-template-rotate"
        sx={{ minHeight: TARGET_PX }}
      >
        {t(`${PREFIX}.panel.rotate`, { deg: props.rotationDeg })}
      </Button>
      <Button
        variant="contained"
        size="small"
        // aria-disabled, not disabled: a disabled button drops the keyboard focus to the page body
        onClick={() => {
          if (known && !props.busy) props.onPlaceCenter();
        }}
        aria-disabled={!known || props.busy}
        data-testid="garden-plan-template-place-center"
        sx={{ minHeight: TARGET_PX }}
      >
        {t(`${PREFIX}.panel.placeCenter`)}
      </Button>
      <Button
        size="small"
        onClick={props.onClose}
        data-testid="garden-plan-template-close"
        sx={{ minHeight: TARGET_PX }}
      >
        {t(`${PREFIX}.panel.close`)}
      </Button>
      <Typography
        variant="body2"
        color="text.secondary"
        role="status"
        data-testid="garden-plan-template-hint"
        sx={{ flexBasis: '100%' }}
      >
        {props.busy
          ? t(`${PREFIX}.panel.placing`)
          : known
            ? props.ghostInvalid
              ? t(`${PREFIX}.panel.hintInvalid`)
              : t(`${PREFIX}.panel.hintPlace`)
            : t(`${PREFIX}.panel.hintPick`)}
      </Typography>
      {catalogue.failed && (
        <Alert
          severity="warning"
          data-testid="garden-plan-template-failed"
          sx={{ flexBasis: '100%' }}
        >
          {t(`${PREFIX}.panel.failed`)}
        </Alert>
      )}
    </Box>
  );
}
