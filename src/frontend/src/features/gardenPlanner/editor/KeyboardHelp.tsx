/**
 * The key reference of the plan editor with the switch for the single-key shortcuts (REQ-053
 * GP-UX-045, WCAG 2.1.4). Opened by the "Keyboard help" button - which is the way in when the
 * `?` shortcut is switched off.
 */
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const KEYS = [
  'arrows',
  'shiftArrows',
  'scroll',
  'pageKeys',
  'enter',
  'del',
  'esc',
  'selectAll',
] as const;

interface KeyboardHelpProps {
  open: boolean;
  onClose: () => void;
  singleKeyShortcuts: boolean;
  onSingleKeyShortcuts: (enabled: boolean) => void;
}

export function KeyboardHelp({
  open,
  onClose,
  singleKeyShortcuts,
  onSingleKeyShortcuts,
}: KeyboardHelpProps) {
  const { t } = useTranslation();
  const prefix = 'pages.gardenPlan.editor.keyboard';
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="garden-plan-keyboard-title"
      data-testid="garden-plan-keyboard-help"
    >
      <DialogTitle id="garden-plan-keyboard-title">{t(`${prefix}.title`)}</DialogTitle>
      <DialogContent>
        <Box
          component="dl"
          sx={{
            m: 0,
            display: 'grid',
            gridTemplateColumns: 'minmax(0, auto) minmax(0, 1fr)',
            columnGap: 2,
            rowGap: 1,
          }}
        >
          {KEYS.map((name) => (
            <Box key={name} sx={{ display: 'contents' }}>
              <Box component="dt" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
                {t(`${prefix}.keys.${name}.keys`)}
              </Box>
              <Box component="dd" sx={{ m: 0, overflowWrap: 'anywhere' }}>
                {t(`${prefix}.keys.${name}.does`)}
              </Box>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {t(`${prefix}.shortcutNote`)}
        </Typography>
        <FormControlLabel
          sx={{ mt: 1, minHeight: 44 }}
          control={
            <Switch
              checked={singleKeyShortcuts}
              onChange={(event) => onSingleKeyShortcuts(event.target.checked)}
              slotProps={{ input: { 'aria-describedby': 'garden-plan-single-key-hint' } }}
            />
          }
          label={t(`${prefix}.singleKeyLabel`)}
        />
        <FormHelperText id="garden-plan-single-key-hint">
          {t(`${prefix}.singleKeyHint`)}
        </FormHelperText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} autoFocus sx={{ minHeight: 44 }}>
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
