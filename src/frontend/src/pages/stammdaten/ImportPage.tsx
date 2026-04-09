import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Select from '@mui/material/Select';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DownloadIcon from '@mui/icons-material/Download';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  clearCurrentJob,
  confirmImportJob,
  uploadFile,
} from '@/store/slices/importSlice';
import { getImportTemplate } from '@/api/endpoints/import';
import type { DuplicateStrategy, EntityType, RowStatus } from '@/api/types';

const STATUS_COLORS: Record<RowStatus, 'success' | 'error' | 'warning'> = {
  valid: 'success',
  invalid: 'error',
  duplicate: 'warning',
};

export default function ImportPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { currentJob, loading, error } = useAppSelector((state) => state.import);

  const [activeStep, setActiveStep] = useState(0);
  const [entityType, setEntityType] = useState<EntityType>('species');
  const [duplicateStrategy, setDuplicateStrategy] =
    useState<DuplicateStrategy>('skip');
  const [file, setFile] = useState<File | null>(null);

  const steps = [
    t('pages.import.stepUpload'),
    t('pages.import.stepPreview'),
    t('pages.import.stepResult'),
  ];

  const handleUpload = useCallback(async () => {
    if (!file) return;
    const result = await dispatch(
      uploadFile({ file, entityType, duplicateStrategy }),
    );
    if (uploadFile.fulfilled.match(result)) {
      setActiveStep(1);
    }
  }, [file, entityType, duplicateStrategy, dispatch]);

  const handleConfirm = useCallback(async () => {
    if (!currentJob) return;
    const result = await dispatch(confirmImportJob(currentJob.key));
    if (confirmImportJob.fulfilled.match(result)) {
      setActiveStep(2);
    }
  }, [currentJob, dispatch]);

  const handleReset = useCallback(() => {
    dispatch(clearCurrentJob());
    setActiveStep(0);
    setFile(null);
  }, [dispatch]);

  const handleDownloadTemplate = useCallback(async () => {
    const csv = await getImportTemplate(entityType);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${entityType}_template.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [entityType]);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('pages.import.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.import.description')}
      </Typography>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} data-testid="import-error">
          {error}
        </Alert>
      )}

      {activeStep === 0 && (
        <Paper sx={{ p: 3 }} data-testid="import-step-upload">
          <Box
            sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: { xs: '100%', sm: 400, md: 500 } }}
          >
            <FormControl fullWidth>
              <InputLabel id="entity-type-label">
                {t('pages.import.entityType')}
              </InputLabel>
              <Select
                labelId="entity-type-label"
                value={entityType}
                label={t('pages.import.entityType')}
                onChange={(e) => setEntityType(e.target.value as EntityType)}
                data-testid="import-entity-type"
              >
                <MenuItem value="species">
                  {t('pages.import.entitySpecies')}
                </MenuItem>
                <MenuItem value="cultivar">
                  {t('pages.import.entityCultivar')}
                </MenuItem>
                <MenuItem value="botanical_family">
                  {t('pages.import.entityFamily')}
                </MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="duplicate-strategy-label">
                {t('pages.import.duplicateStrategy')}
              </InputLabel>
              <Select
                labelId="duplicate-strategy-label"
                value={duplicateStrategy}
                label={t('pages.import.duplicateStrategy')}
                onChange={(e) =>
                  setDuplicateStrategy(e.target.value as DuplicateStrategy)
                }
                data-testid="import-duplicate-strategy"
              >
                <MenuItem value="skip">
                  {t('pages.import.strategySkip')}
                </MenuItem>
                <MenuItem value="update">
                  {t('pages.import.strategyUpdate')}
                </MenuItem>
                <MenuItem value="fail">
                  {t('pages.import.strategyFail')}
                </MenuItem>
              </Select>
            </FormControl>

            <Box>
              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUploadIcon />}
                data-testid="import-file-select"
              >
                {file ? file.name : t('pages.import.selectFile')}
                <input
                  type="file"
                  hidden
                  accept=".csv,.tsv,.txt"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </Button>
              {file && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  {t('pages.import.fileInfo', {
                    size: (file.size / 1024).toFixed(1),
                  })}
                </Typography>
              )}
            </Box>

            <Button
              variant="text"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              data-testid="import-download-template"
            >
              {t('pages.import.downloadTemplate')}
            </Button>

            <Box>
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!file || loading}
                startIcon={<CloudUploadIcon />}
                data-testid="import-upload-button"
              >
                {t('pages.import.upload')}
              </Button>
              {!file && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  {t('pages.import.selectFileHint')}
                </Typography>
              )}
            </Box>
          </Box>
        </Paper>
      )}

      {activeStep === 1 && currentJob && (
        <Paper sx={{ p: 3 }} data-testid="import-step-preview">
          <Typography variant="subtitle1" gutterBottom>
            {t('pages.import.file')}: {currentJob.filename} &mdash;{' '}
            {currentJob.row_count} {t('pages.import.rows')}
          </Typography>

          <TableContainer sx={{ maxHeight: 400, mb: 2 }}>
            <Table stickyHeader size="small" aria-label={t('pages.import.stepPreview')}>
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>{t('pages.import.data')}</TableCell>
                  <TableCell>{t('pages.import.status')}</TableCell>
                  <TableCell>{t('pages.import.errors')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentJob.preview_rows.map((row) => (
                  <TableRow key={row.row_number}>
                    <TableCell>{row.row_number}</TableCell>
                    <TableCell
                      sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                    >
                      {JSON.stringify(row.data)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={row.status}
                        color={STATUS_COLORS[row.status]}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {row.errors.length > 0 && (
                        <Tooltip
                          title={row.errors
                            .map((e) => `${e.field}: ${e.message}`)
                            .join(', ')}
                        >
                          <Chip
                            label={`${row.errors.length} ${t('pages.import.errors')}`}
                            color="error"
                            size="small"
                            variant="outlined"
                          />
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={() => {
                setActiveStep(0);
                dispatch(clearCurrentJob());
              }}
              data-testid="import-back-button"
            >
              {t('common.back')}
            </Button>
            <Button
              variant="contained"
              onClick={handleConfirm}
              disabled={loading}
              startIcon={<CheckCircleIcon />}
              data-testid="import-confirm-button"
            >
              {t('pages.import.confirm')}
            </Button>
          </Box>
        </Paper>
      )}

      {activeStep === 2 && currentJob?.result && (
        <Paper sx={{ p: 3 }} data-testid="import-step-result">
          <Typography variant="h6" gutterBottom>
            {t('pages.import.resultTitle')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, mb: 2, flexWrap: 'wrap' }}>
            <Chip
              label={`${t('pages.import.created')}: ${currentJob.result.created}`}
              color="success"
            />
            {currentJob.result.updated > 0 && (
              <Chip
                label={`${t('pages.import.updated')}: ${currentJob.result.updated}`}
                color="info"
              />
            )}
            <Chip
              label={`${t('pages.import.skipped')}: ${currentJob.result.skipped}`}
              color="warning"
            />
            <Chip
              label={`${t('pages.import.failed')}: ${currentJob.result.failed}`}
              color="error"
            />
          </Box>
          {currentJob.result.errors.length > 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {currentJob.result.errors.map((e, i) => (
                <div key={i}>{e}</div>
              ))}
            </Alert>
          )}
          <Button
            variant="contained"
            onClick={handleReset}
            data-testid="import-new-button"
          >
            {t('pages.import.newImport')}
          </Button>
        </Paper>
      )}
    </Box>
  );
}
