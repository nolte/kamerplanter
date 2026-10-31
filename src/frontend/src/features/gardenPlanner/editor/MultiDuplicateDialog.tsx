/**
 * "Duplicate several times" (REQ-053 GP-FR-025 SHOULD, F-10): count, direction, spacing and a naming scheme
 * ("Parzelle {n}") for the many equal plots of a community garden. The dialog collects the numbers and shows the
 * names it will give; the editor checks quota and validation and answers with the reason of a refusal, which is
 * explained here - nothing is created then. Slots are not copied; the panel offers a layout afterwards.
 * Its own lazy chunk.
 */
import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import {
  MAX_MULTI_COPIES,
  multiCopyName,
  type MultiDirection,
  type MultiDuplicateOptions,
  type MultiRefusal,
} from './tools/duplicate';
import { roundLength } from '../model/geometry';
import type { LengthUnit } from '../model/units';
import { parseDecimal } from './tools/panelFields';

const PREFIX = 'pages.gardenPlan.editor.multiDuplicate';
const DIRECTIONS: readonly MultiDirection[] = ['right', 'left', 'up', 'down'];
/** The spacing the dialog opens with, in metres. */
const DEFAULT_SPACING_M = 0.5;
/** Metres per unit of the spacing field (GP-FR-004: shown in the chosen unit, stored in metres). */
const METRES_PER: Record<LengthUnit, number> = { m: 1, cm: 0.01 };

interface MultiDuplicateDialogProps {
  open: boolean;
  /** How many selected beds (roots) get a name from the scheme; 0 = only garden objects, which keep theirs. */
  rootBeds: number;
  /** The length unit the user chose for the editor (`useLengthUnit`); the spacing field shows and takes it. */
  unit: LengthUnit;
  /** Runs the duplication; resolves with the refusal or `null` when it was done. */
  onRun: (options: MultiDuplicateOptions) => MultiRefusal | null;
  onClose: () => void;
}

/**
 * A length for a text field in the user's language: the decimal comma in German ("0,5"), no thousands separator -
 * `parseDecimal` reads both separators back, so the prefilled value round-trips unchanged.
 */
function formatLength(value: number, language: string): string {
  return new Intl.NumberFormat(language, { useGrouping: false, maximumFractionDigits: 3 }).format(
    roundLength(value),
  );
}

function Form({ rootBeds, unit, onRun, onClose }: Omit<MultiDuplicateDialogProps, 'open'>) {
  const { t, i18n } = useTranslation();
  const [count, setCount] = useState('5');
  const [direction, setDirection] = useState<MultiDirection>('right');
  const [spacing, setSpacing] = useState(() =>
    formatLength(DEFAULT_SPACING_M / METRES_PER[unit], i18n.language),
  );
  const [scheme, setScheme] = useState(() => t(`${PREFIX}.defaultScheme`));
  const [start, setStart] = useState('1');
  const [refusal, setRefusal] = useState<MultiRefusal | null>(null);

  const countN = parseDecimal(count);
  const spacingN = parseDecimal(spacing);
  const spacingM = spacingN === null ? null : roundLength(spacingN * METRES_PER[unit]);
  const startN = parseDecimal(start);
  const countOk =
    countN !== null && Number.isInteger(countN) && countN >= 1 && countN <= MAX_MULTI_COPIES;
  const spacingOk = spacingM !== null && spacingM >= 0;
  const startOk = startN !== null && Number.isInteger(startN);
  const valid = countOk && spacingOk && startOk;

  const preview = useMemo(() => {
    if (!countOk || !startOk || scheme.trim() === '' || rootBeds === 0) return null;
    // Every copy of every selected bed takes the next number, in the order the beds are copied.
    const total = countN * rootBeds;
    const first = multiCopyName(scheme, startN);
    const last = multiCopyName(scheme, startN + total - 1);
    return total === 1 ? first : `${first} … ${last}`;
  }, [countN, countOk, rootBeds, scheme, startN, startOk]);

  const edit =
    <T,>(setter: (value: T) => void) =>
    (value: T) => {
      setter(value);
      setRefusal(null);
    };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!valid) return;
    setRefusal(onRun({ count: countN, direction, spacingM, scheme, startNumber: startN }));
  };

  const field = (
    id: string,
    label: string,
    value: string,
    onChange: (value: string) => void,
    ok: boolean,
    helper: string,
    unit?: string,
  ) => (
    <TextField
      size="small"
      label={label}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required
      error={!ok}
      helperText={ok ? helper : t(`${PREFIX}.invalid`)}
      slotProps={{
        htmlInput: { inputMode: 'decimal', 'data-testid': `garden-plan-multi-${id}` },
        input: unit ? { endAdornment: unit } : undefined,
      }}
      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
    />
  );

  return (
    <form onSubmit={submit} noValidate>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.intro`)}
          </Typography>
          {field(
            'count',
            t(`${PREFIX}.count`),
            count,
            edit(setCount),
            countOk,
            t(`${PREFIX}.countHelper`, { max: MAX_MULTI_COPIES }),
          )}
          <TextField
            select
            size="small"
            label={t(`${PREFIX}.direction`)}
            value={direction}
            onChange={(event) => edit(setDirection)(event.target.value as MultiDirection)}
            slotProps={{ htmlInput: { 'data-testid': 'garden-plan-multi-direction' } }}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          >
            {DIRECTIONS.map((item) => (
              <MenuItem key={item} value={item} sx={{ minHeight: 48 }}>
                {t(`${PREFIX}.directions.${item}`)}
              </MenuItem>
            ))}
          </TextField>
          {field(
            'spacing',
            t(`${PREFIX}.spacing`),
            spacing,
            edit(setSpacing),
            spacingOk,
            t(`${PREFIX}.spacingHelper`),
            unit,
          )}
          <TextField
            size="small"
            label={t(`${PREFIX}.scheme`)}
            value={scheme}
            onChange={(event) => edit(setScheme)(event.target.value)}
            helperText={t(`${PREFIX}.schemeHelper`)}
            slotProps={{ htmlInput: { maxLength: 100, 'data-testid': 'garden-plan-multi-scheme' } }}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          />
          {field(
            'start',
            t(`${PREFIX}.start`),
            start,
            edit(setStart),
            startOk,
            t(`${PREFIX}.startHelper`),
          )}
          {rootBeds === 0 && (
            <Typography variant="body2" role="status" data-testid="garden-plan-multi-no-names">
              {t(`${PREFIX}.noNames`)}
            </Typography>
          )}
          {preview && (
            <Typography variant="body2" role="status" data-testid="garden-plan-multi-preview">
              {t(`${PREFIX}.preview`, { names: preview })}
            </Typography>
          )}
          <Typography variant="caption" color="text.secondary">
            {t(`${PREFIX}.slotsNote`)}
          </Typography>
          {refusal && (
            <Alert severity="error" role="alert" data-testid="garden-plan-multi-error">
              {t(`pages.gardenPlan.editor.notice.${refusal.code}`, {
                defaultValue: t('pages.gardenPlan.editor.notice.generic'),
              })}
              {refusal.failedName !== undefined
                ? ` ${t(`${PREFIX}.failedCopyNamed`, { name: refusal.failedName })}`
                : refusal.failedCopy !== undefined &&
                  ` ${t(`${PREFIX}.failedCopy`, { n: refusal.failedCopy })}`}
            </Alert>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }} data-testid="garden-plan-multi-cancel">
          {t('pages.gardenPlan.editor.draw.cancel')}
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={!valid}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-multi-submit"
        >
          {t(`${PREFIX}.submit`)}
        </Button>
      </DialogActions>
    </form>
  );
}

export default function MultiDuplicateDialog(props: MultiDuplicateDialogProps) {
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
      aria-labelledby="garden-plan-multi-title"
      data-testid="garden-plan-multi-dialog"
    >
      <DialogTitle id="garden-plan-multi-title">{t(`${PREFIX}.title`)}</DialogTitle>
      {open && <Form {...rest} />}
    </Dialog>
  );
}
