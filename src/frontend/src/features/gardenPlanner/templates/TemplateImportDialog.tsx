/**
 * "Import template" (REQ-053 GP-FR-173, WP 9.9): the user picks a template file, the server checks it (dry run)
 * and answers a report; only the confirmation writes. A taken name answers a free one, which the user can take
 * or change before checking again. Its own lazy chunk: the template panel does not carry it.
 */
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import type { TFunction } from 'i18next';
import {
  MAX_TEMPLATE_FILE_BYTES,
  describeImportFailure,
  importBedTemplate,
  type BedTemplateExchangeFile,
  type BedTemplateImportReport,
  type TemplateImportFailure,
} from './templateExchange';

const PREFIX = 'pages.gardenPlan.editor.templates.exchange';

interface TemplateImportDialogProps {
  open: boolean;
  /** Called with the new template's key once the import is written. */
  onImported: (key: string) => void;
  onClose: () => void;
}

function shapeText(t: TFunction, template: BedTemplateExchangeFile): string {
  const geometry = template.default_geometry;
  if (geometry.kind === 'rect') {
    return t(`${PREFIX}.shape.rect`, { width: geometry.width_m, length: geometry.length_m });
  }
  if (geometry.kind === 'circle') {
    return t(`${PREFIX}.shape.circle`, { diameter: geometry.radius_m * 2 });
  }
  if (geometry.kind === 'polygon') {
    return t(`${PREFIX}.shape.polygon`, { count: geometry.points.length });
  }
  return geometry.kind;
}

function failureText(t: TFunction, failure: TemplateImportFailure): string {
  if (failure.kind === 'name_taken') return t(`${PREFIX}.error.nameTaken`);
  if (failure.kind === 'too_large') return t(`${PREFIX}.error.tooLarge`);
  if (failure.kind === 'forbidden') return t(`${PREFIX}.error.forbidden`);
  if (failure.kind === 'code') {
    return t(`${PREFIX}.error.codes.${failure.code}`, {
      defaultValue: t(`${PREFIX}.error.generic`),
    });
  }
  return t(`${PREFIX}.error.generic`);
}

function Report({ report }: { report: BedTemplateImportReport }) {
  const { t } = useTranslation();
  const { template } = report;
  return (
    <Box data-testid="garden-plan-template-import-report" sx={{ mt: 2 }}>
      <Typography variant="subtitle2">{t(`${PREFIX}.report.title`)}</Typography>
      <Typography variant="body2">{t(`${PREFIX}.report.name`, { name: template.name })}</Typography>
      <Typography variant="body2">
        {t(`${PREFIX}.report.shape`, { shape: shapeText(t, template) })}
      </Typography>
      {template.height_m != null && (
        <Typography variant="body2">
          {t(`${PREFIX}.report.height`, { height: template.height_m })}
        </Typography>
      )}
      {(template.default_layout.row_spacing_cm != null ||
        template.default_layout.spacing_cm != null) && (
        <Typography variant="body2">
          {t(`${PREFIX}.report.grid`, {
            rows: template.default_layout.row_spacing_cm ?? '–',
            spacing: template.default_layout.spacing_cm ?? '–',
          })}
        </Typography>
      )}
      {report.migrated && (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.report.migrated`, { version: report.schema_version })}
        </Typography>
      )}
      {report.dropped_fields.length + report.unknown_fields_ignored > 0 && (
        <Alert severity="info" sx={{ mt: 1 }} data-testid="garden-plan-template-import-dropped">
          {t(`${PREFIX}.report.dropped`, {
            count: report.dropped_fields.length + report.unknown_fields_ignored,
          })}
        </Alert>
      )}
    </Box>
  );
}

function Body({ onImported, onClose }: Omit<TemplateImportDialogProps, 'open'>) {
  const { t } = useTranslation();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [report, setReport] = useState<BedTemplateImportReport | null>(null);
  const [failure, setFailure] = useState<TemplateImportFailure | null>(null);
  const [busy, setBusy] = useState(false);

  // The name the shown report was checked with (`null` = the file's own): exactly what the confirmation sends.
  const [checkedName, setCheckedName] = useState<string | null>(null);

  const refuse = (error: unknown) => {
    const refusal = describeImportFailure(error);
    setFailure(refusal);
    if (refusal.kind === 'name_taken' && refusal.suggestedName) setName(refusal.suggestedName);
  };

  const check = async (picked: File, override: string | null) => {
    setReport(null);
    setFailure(null);
    if (picked.size > MAX_TEMPLATE_FILE_BYTES) {
      setFailure({ kind: 'too_large' });
      return;
    }
    setBusy(true);
    try {
      const checked = await importBedTemplate(picked, { dryRun: true, name: override });
      setCheckedName(override);
      setReport(checked);
    } catch (error) {
      refuse(error);
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!file || !report || busy) return;
    setBusy(true);
    try {
      const applied = await importBedTemplate(file, { dryRun: false, name: checkedName });
      if (applied.created_key) onImported(applied.created_key);
    } catch (error) {
      // A name taken in between (409) proposes a free one exactly like the check; confirming needs a new check.
      setReport(null);
      refuse(error);
    } finally {
      setBusy(false);
    }
  };

  const nameAsked = failure?.kind === 'name_taken' || checkedName !== null || name !== '';
  return (
    <>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t(`${PREFIX}.intro`)}
        </Typography>
        <input
          ref={input}
          type="file"
          accept=".json,application/json"
          hidden
          data-testid="garden-plan-template-import-file"
          onChange={(event) => {
            const picked = event.target.files?.[0] ?? null;
            event.target.value = '';
            if (!picked) return;
            setFile(picked);
            setName('');
            setCheckedName(null);
            void check(picked, null);
          }}
        />
        <Button
          variant="outlined"
          startIcon={<UploadFileIcon />}
          onClick={() => input.current?.click()}
          disabled={busy}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-template-import-pick"
        >
          {file ? t(`${PREFIX}.pickOther`) : t(`${PREFIX}.pick`)}
        </Button>
        {file && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t(`${PREFIX}.picked`, { file: file.name })}
          </Typography>
        )}
        {busy && (
          <Typography variant="body2" role="status" sx={{ mt: 1 }}>
            {t(`${PREFIX}.checking`)}
          </Typography>
        )}
        {failure && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="garden-plan-template-import-error">
            {failureText(t, failure)}
          </Alert>
        )}
        {nameAsked && file && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', mt: 2 }}>
            <TextField
              size="small"
              label={t(`${PREFIX}.name`)}
              value={name}
              onChange={(event) => {
                // A changed name was not checked: the report goes, "Import" waits for the next check.
                setName(event.target.value);
                setReport(null);
              }}
              slotProps={{
                htmlInput: { maxLength: 200, 'data-testid': 'garden-plan-template-import-name' },
              }}
              sx={{ flex: '1 1 220px', '& .MuiInputBase-root': { minHeight: 48 } }}
            />
            <Button
              onClick={() => void check(file, name.trim() || null)}
              disabled={busy || name.trim() === ''}
              sx={{ minHeight: 48 }}
              data-testid="garden-plan-template-import-recheck"
            >
              {t(`${PREFIX}.recheck`)}
            </Button>
          </Box>
        )}
        {report && <Report report={report} />}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }} data-testid="garden-plan-template-import-cancel">
          {t('pages.gardenPlan.editor.draw.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void confirm()}
          disabled={busy || report === null}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-template-import-confirm"
        >
          {t(`${PREFIX}.confirm`)}
        </Button>
      </DialogActions>
    </>
  );
}

export default function TemplateImportDialog(props: TemplateImportDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { open, ...rest } = props;
  return (
    <Dialog
      open={open}
      onClose={props.onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="garden-plan-template-import-title"
      data-testid="garden-plan-template-import-dialog"
    >
      <DialogTitle id="garden-plan-template-import-title">{t(`${PREFIX}.title`)}</DialogTitle>
      {open && <Body {...rest} />}
    </Dialog>
  );
}
