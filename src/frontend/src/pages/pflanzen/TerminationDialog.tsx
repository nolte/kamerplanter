import { useEffect, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import RadioGroup from '@mui/material/RadioGroup';
import Radio from '@mui/material/Radio';
import Checkbox from '@mui/material/Checkbox';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';
import { getTerminationOptions } from '@/api/endpoints/plantTermination';
import { captureHandledError } from '@/observability/errorTracking';
import type {
  FailureCauseClass,
  PathogenConfirmationSource,
  RemovePlantRequest,
  SoilHazard,
  TerminationCause,
  TerminationOptions,
  TerminationType,
} from '@/api/types';

/** Selectable termination types (REQ-003 E5). Order = decreasing likelihood. */
const TERMINATION_TYPES: TerminationType[] = ['harvested', 'senesced', 'died', 'cancelled'];

type WiltAnswer = '' | 'yes' | 'no';
type OptionsState = 'loading' | 'ready' | 'error';

interface Props {
  open: boolean;
  /** The plant being ended; the dialog loads its cause-class options (`GET /{key}/termination-options`). */
  plantKey: string;
  plantName: string;
  /** Called with the classified removal body. An empty object = plain removal. */
  onConfirm: (body: RemovePlantRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

/**
 * Removal dialog that classifies how a plant's lifecycle ended (REQ-003 E5).
 *
 * The termination type is optional — confirming without a selection performs a
 * plain removal (backward compatible). Selecting `died` reveals a required cause
 * and, from the cause, the cause class (#2888): the pre-fill table comes from the
 * server, which also validates the result. Disease and pest need a foliar/soil
 * choice; heat, drought, waterlogging and — on wilt-prone families — `unknown`
 * ask the wilt follow-up; a soil-borne class may name a pathogen with whether and
 * by whom it was confirmed.
 */
export default function TerminationDialog({ open, plantKey, plantName, onConfirm, onCancel, loading = false }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  // The form lives in its own component: the Dialog unmounts it once closed, so every opening starts with an empty
  // form and a fresh options load - no reset effect needed.
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="termination-dialog-title"
      aria-describedby="termination-dialog-description"
      role="alertdialog"
      data-testid="termination-dialog"
    >
      <TerminationForm
        key={plantKey}
        plantKey={plantKey}
        plantName={plantName}
        onConfirm={onConfirm}
        onCancel={onCancel}
        loading={loading}
      />
    </Dialog>
  );
}

type FormProps = Omit<Props, 'open'> & { loading: boolean };

function TerminationForm({ plantKey, plantName, onConfirm, onCancel, loading }: FormProps) {
  const { t } = useTranslation();

  const [terminationType, setTerminationType] = useState<TerminationType | ''>('');
  // The cause the user picked; until then the suggested cause of the options stands (premature bolting, E6).
  const [causeChoice, setCauseChoice] = useState<TerminationCause | ''>('');
  // The class the user picked or answered; null = the pre-fill of the cause.
  const [classChoice, setClassChoice] = useState<FailureCauseClass | null>(null);
  const [wilt, setWilt] = useState<WiltAnswer>('');
  // Whether the current class came from a wilt "yes" (and not from the picker): only then may a "no" take it back.
  const [classFromWilt, setClassFromWilt] = useState(false);
  const [pathogen, setPathogen] = useState<SoilHazard | ''>('');
  const [confirmed, setConfirmed] = useState(false);
  const [source, setSource] = useState<PathogenConfirmationSource | ''>('');
  const [options, setOptions] = useState<TerminationOptions | null>(null);
  const [optionsState, setOptionsState] = useState<OptionsState>('loading');
  const [attempt, setAttempt] = useState(0);

  // Load this plant's options on mount and on every retry.
  useEffect(() => {
    let cancelled = false;
    getTerminationOptions(plantKey)
      .then((loaded) => {
        if (cancelled) return;
        setOptions(loaded);
        setOptionsState('ready');
      })
      .catch((err: unknown) => {
        captureHandledError(err, { source: 'TerminationDialog.options' });
        if (!cancelled) setOptionsState('error');
      });
    return () => {
      cancelled = true;
    };
  }, [plantKey, attempt]);

  const retry = () => {
    setOptionsState('loading');
    setAttempt((n) => n + 1);
  };

  const isDied = terminationType === 'died';
  const suggestedCause = options?.suggested_cause ?? null;
  const terminationCause: TerminationCause | '' = causeChoice || (isDied && suggestedCause ? suggestedCause : '');

  const rule = useMemo(
    () => options?.rules.find((r) => r.termination_cause === terminationCause) ?? null,
    [options, terminationCause],
  );
  const failureClass: FailureCauseClass | '' = classChoice ?? rule?.prefill ?? '';

  const clearPathogen = () => {
    setPathogen('');
    setConfirmed(false);
    setSource('');
  };

  const selectCause = (cause: TerminationCause | '') => {
    setCauseChoice(cause);
    setClassChoice(null);
    setWilt('');
    setClassFromWilt(false);
    clearPathogen();
  };

  const wiltClass = options?.wilt_follow_up_class ?? null;
  const asksWilt = rule?.asks_wilt_follow_up ?? false;
  const wiltRecorded = wiltClass !== null && failureClass === wiltClass;
  // A picker only when the cause offers more than its pre-fill (plus the wilt class the question already offers).
  const showPicker = rule !== null && rule.choices.length > (asksWilt ? 2 : 1);
  const pathogenClasses = options?.pathogen_classes;
  const isSoilBorne = failureClass !== '' && (pathogenClasses ?? []).includes(failureClass);

  const changeClass = (next: FailureCauseClass | null) => {
    setClassChoice(next);
    const resolved = next ?? rule?.prefill ?? null;
    if (resolved === null || !(pathogenClasses ?? []).includes(resolved)) clearPathogen();
  };

  const pickClass = (next: FailureCauseClass) => {
    setClassFromWilt(false);
    changeClass(next);
  };

  const answerWilt = (answer: WiltAnswer) => {
    setWilt(answer);
    if (answer === 'yes' && wiltClass) {
      setClassFromWilt(true);
      changeClass(wiltClass);
    }
    // A "no" only takes back what a "yes" recorded; a class picked in the picker stays, with its pathogen.
    if (answer === 'no' && classFromWilt) {
      setClassFromWilt(false);
      changeClass(null);
    }
  };

  const changePathogen = (next: SoilHazard | '') => {
    setPathogen(next);
    if (next === '') {
      setConfirmed(false);
      setSource('');
    }
  };

  const missing: string | null = useMemo(() => {
    if (!isDied) return null;
    if (optionsState === 'error') return t('pages.plantInstances.termination.optionsError');
    if (optionsState === 'loading') return t('pages.plantInstances.termination.optionsLoading');
    if (terminationCause === '') return t('pages.plantInstances.termination.confirmDisabledHint');
    if (failureClass === '') return t('pages.plantInstances.termination.classRequiredHint');
    if (confirmed && source === '') return t('pages.plantInstances.termination.sourceRequiredHint');
    return null;
  }, [isDied, terminationCause, optionsState, failureClass, confirmed, source, t]);

  const canConfirm = !loading && missing === null;
  const blockedReasonId = useId();
  const blockedReason = !loading && missing !== null ? missing : null;

  const body = useMemo<RemovePlantRequest>(() => {
    if (terminationType === '') return {};
    if (terminationType !== 'died') return { termination_type: terminationType };
    const died: RemovePlantRequest = {
      termination_type: 'died',
      termination_cause: terminationCause || undefined,
      failure_cause_class: failureClass || undefined,
    };
    if (isSoilBorne && pathogen !== '') {
      died.failure_pathogen = pathogen;
      died.failure_pathogen_confirmed = confirmed;
      if (confirmed && source !== '') died.failure_pathogen_source = source;
    }
    return died;
  }, [terminationType, terminationCause, failureClass, isSoilBorne, pathogen, confirmed, source]);

  const handleConfirm = () => {
    if (!canConfirm) return;
    onConfirm(body);
  };

  return (
    <>
      <DialogTitle id="termination-dialog-title">{t('pages.plantInstances.termination.title')}</DialogTitle>
      <DialogContent>
        <DialogContentText id="termination-dialog-description" sx={{ mb: 2 }}>
          {t('pages.plantInstances.termination.intro', { name: plantName })}
        </DialogContentText>

        <Alert severity="warning" sx={{ mb: 2 }} data-testid="termination-irreversible-warning">
          {t('pages.plantInstances.termination.irreversibleNote')}
        </Alert>

        <TextField
          select
          fullWidth
          autoFocus
          label={t('pages.plantInstances.termination.typeLabel')}
          value={terminationType}
          onChange={(e) => setTerminationType(e.target.value as TerminationType | '')}
          helperText={t('pages.plantInstances.termination.typeHelper')}
          disabled={loading}
          sx={{ mb: 2, mt: 1 }}
          data-testid="termination-type-select"
          slotProps={{ select: { displayEmpty: true } }}
        >
          <MenuItem value="">
            <em>{t('pages.plantInstances.termination.typeUnspecified')}</em>
          </MenuItem>
          {TERMINATION_TYPES.map((tt) => (
            <MenuItem key={tt} value={tt} data-testid={`termination-type-${tt}`}>
              {t(`enums.terminationType.${tt}`)}
            </MenuItem>
          ))}
        </TextField>

        {isDied && (
          <Box data-testid="termination-cause-block">
            <Alert severity="info" sx={{ mb: 2 }}>
              {t('pages.plantInstances.termination.causeExplainer')}
            </Alert>

            {optionsState === 'loading' && (
              <Box
                role="status"
                sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}
                data-testid="loading-skeleton"
              >
                <CircularProgress size={20} />
                <Typography variant="body2">{t('pages.plantInstances.termination.optionsLoading')}</Typography>
              </Box>
            )}

            {optionsState === 'error' && (
              <Alert
                severity="error"
                sx={{ mb: 2 }}
                data-testid="termination-options-error"
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={retry}
                    data-testid="termination-options-retry"
                  >
                    {t('pages.plantInstances.termination.optionsRetry')}
                  </Button>
                }
              >
                {t('pages.plantInstances.termination.optionsError')}
              </Alert>
            )}

            {options && (
              <>
                {suggestedCause && terminationCause === suggestedCause && (
                  <Alert severity="info" sx={{ mb: 2 }} data-testid="termination-cause-suggested">
                    {t('pages.plantInstances.termination.boltingSuggested')}
                  </Alert>
                )}
                <TextField
                  select
                  fullWidth
                  required
                  label={t('pages.plantInstances.termination.causeLabel')}
                  value={terminationCause}
                  onChange={(e) => selectCause(e.target.value as TerminationCause | '')}
                  helperText={t('pages.plantInstances.termination.causeHelper')}
                  error={terminationCause === ''}
                  disabled={loading}
                  sx={{ mb: 2 }}
                  data-testid="termination-cause-select"
                >
                  {options.rules.map((r) => (
                    <MenuItem
                      key={r.termination_cause}
                      value={r.termination_cause}
                      data-testid={`termination-cause-${r.termination_cause}`}
                    >
                      {t(`enums.terminationCause.${r.termination_cause}`)}
                    </MenuItem>
                  ))}
                </TextField>
              </>
            )}

            {rule && asksWilt && (
              <FormControl component="fieldset" sx={{ mb: 2, display: 'block' }} data-testid="termination-wilt-question">
                <FormLabel component="legend">{t('pages.plantInstances.termination.wiltQuestion')}</FormLabel>
                <RadioGroup
                  row
                  value={classFromWilt && wiltRecorded ? 'yes' : wilt === 'no' ? 'no' : ''}
                  onChange={(e) => answerWilt(e.target.value as WiltAnswer)}
                >
                  <FormControlLabel
                    value="yes"
                    control={<Radio slotProps={{ input: { 'data-testid': 'termination-wilt-yes' } as object }} />}
                    label={t('pages.plantInstances.termination.wiltYes')}
                    disabled={loading}
                  />
                  <FormControlLabel
                    value="no"
                    control={<Radio slotProps={{ input: { 'data-testid': 'termination-wilt-no' } as object }} />}
                    label={t('pages.plantInstances.termination.wiltNo')}
                    disabled={loading}
                  />
                </RadioGroup>
                <FormHelperText>
                  {wiltRecorded
                    ? t('pages.plantInstances.termination.wiltYesResult')
                    : t('pages.plantInstances.termination.wiltHelper')}
                </FormHelperText>
              </FormControl>
            )}

            {rule && showPicker && (
              <FormControl
                component="fieldset"
                required
                error={failureClass === ''}
                sx={{ mb: 2, display: 'block' }}
                data-testid="termination-class-picker"
              >
                <FormLabel component="legend">{t('pages.plantInstances.termination.classLabel')}</FormLabel>
                <RadioGroup value={failureClass} onChange={(e) => pickClass(e.target.value as FailureCauseClass)}>
                  {rule.choices.map((cls) => (
                    <FormControlLabel
                      key={cls}
                      value={cls}
                      control={<Radio slotProps={{ input: { 'data-testid': `termination-class-${cls}` } as object }} />}
                      label={t(`enums.failureCauseClass.${cls}`)}
                      disabled={loading}
                    />
                  ))}
                </RadioGroup>
                <FormHelperText>
                  {rule.prefill === null
                    ? t('pages.plantInstances.termination.classHelperRequired')
                    : t('pages.plantInstances.termination.classPickerHelper')}
                </FormHelperText>
              </FormControl>
            )}

            {rule && !showPicker && failureClass !== '' && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }} data-testid="termination-class-prefilled">
                {failureClass === rule.prefill
                  ? t('pages.plantInstances.termination.classPrefilled', {
                      label: t(`enums.failureCauseClass.${failureClass}`),
                    })
                  : t('pages.plantInstances.termination.classRecorded', {
                      label: t(`enums.failureCauseClass.${failureClass}`),
                    })}
              </Typography>
            )}

            {options && isSoilBorne && (
              <Box data-testid="termination-pathogen-block">
                <TextField
                  select
                  fullWidth
                  label={t('pages.plantInstances.termination.pathogenLabel')}
                  value={pathogen}
                  onChange={(e) => changePathogen(e.target.value as SoilHazard | '')}
                  helperText={t('pages.plantInstances.termination.pathogenHelper')}
                  disabled={loading}
                  sx={{ mb: 1 }}
                  data-testid="form-field-failure-pathogen"
                  slotProps={{ select: { displayEmpty: true } }}
                >
                  <MenuItem value="">
                    <em>{t('pages.plantInstances.termination.pathogenNone')}</em>
                  </MenuItem>
                  {options.pathogens.map((hazard) => (
                    <MenuItem key={hazard} value={hazard} data-testid={`termination-pathogen-${hazard}`}>
                      {t(`enums.soilHazard.${hazard}`)}
                    </MenuItem>
                  ))}
                </TextField>

                {pathogen !== '' && (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={confirmed}
                        onChange={(e) => {
                          setConfirmed(e.target.checked);
                          if (!e.target.checked) setSource('');
                        }}
                        slotProps={{ input: { 'data-testid': 'termination-pathogen-confirmed' } as object }}
                      />
                    }
                    label={t('pages.plantInstances.termination.confirmedLabel')}
                    disabled={loading}
                    sx={{ display: 'block', mb: 1 }}
                  />
                )}

                {pathogen !== '' && confirmed && (
                  <FormControl
                    component="fieldset"
                    required
                    error={source === ''}
                    sx={{ display: 'block', mb: 1 }}
                    data-testid="termination-pathogen-source"
                  >
                    <FormLabel component="legend">{t('pages.plantInstances.termination.sourceLabel')}</FormLabel>
                    <RadioGroup value={source} onChange={(e) => setSource(e.target.value as PathogenConfirmationSource)}>
                      {options.confirmation_sources.map((src) => (
                        <FormControlLabel
                          key={src}
                          value={src}
                          control={<Radio slotProps={{ input: { 'data-testid': `termination-source-${src}` } as object }} />}
                          label={t(`enums.pathogenConfirmationSource.${src}`)}
                          disabled={loading}
                        />
                      ))}
                    </RadioGroup>
                  </FormControl>
                )}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={loading} data-testid="termination-cancel">
          {t('common.cancel')}
        </Button>
        {/* The reason the confirm is blocked, for keyboard and screen-reader users too (the tooltip is hover-only). */}
        {blockedReason !== null && (
          <Box component="span" id={blockedReasonId} sx={visuallyHidden} data-testid="termination-confirm-blocked-reason">
            {blockedReason}
          </Box>
        )}
        <Tooltip title={blockedReason ?? ''}>
          <span>
            <Button
              variant="contained"
              color="error"
              onClick={handleConfirm}
              disabled={!canConfirm}
              aria-describedby={blockedReason !== null ? blockedReasonId : undefined}
              startIcon={loading ? <CircularProgress size={16} color="inherit" /> : undefined}
              data-testid="termination-confirm"
            >
              {t('pages.plantInstances.remove')}
            </Button>
          </span>
        </Tooltip>
      </DialogActions>
    </>
  );
}
