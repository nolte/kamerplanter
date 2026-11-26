import { useCallback, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { localizedText } from '@/utils/localizedText';
import FormDialog from '@/components/form/FormDialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { Controller } from 'react-hook-form';
import { useDialogForm } from '@/hooks/useDialogForm';
import { useFormFieldViolations } from '@/hooks/useFieldViolations';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import OptionsLoadError from '@/components/common/OptionsLoadError';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseDefinition, PhaseSequenceEntry } from '@/api/types';

const schema = z.object({
  phase_definition_key: z.string().min(1),
  override_duration_days: z.number().min(1).nullable(),
  is_terminal: z.boolean(),
  allows_harvest: z.boolean(),
  is_recurring: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  sequenceKey: string;
  entry?: PhaseSequenceEntry;
  onSaved: () => void;
}

export default function PhaseSequenceEntryDialog({
  open,
  onClose,
  sequenceKey,
  entry,
  onSaved,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!entry;

  // A failed read is shown with a retry, never as an empty picker (#3037).
  const loadDefinitions = useCallback(
    (): Promise<PhaseDefinition[]> => phaseSequenceApi.listAllPhaseDefinitions(),
    [],
  );
  const definitionsLoad = useAsyncOptions(loadDefinitions, { enabled: open });
  const definitionOptions = definitionsLoad.options;
  const definitionsLoading = definitionsLoad.loading;

  const defaultValues: FormData = {
    phase_definition_key: '',
    override_duration_days: null,
    is_terminal: false,
    allows_harvest: false,
    is_recurring: false,
  };

  const { control, handleSubmit, reset } = useDialogForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues,
  });
  const applyFieldViolation = useFormFieldViolations(control);

  useEffect(() => {
    if (open && entry) {
      reset({
        phase_definition_key: entry.phase_definition_key,
        override_duration_days: entry.override_duration_days,
        is_terminal: entry.is_terminal,
        allows_harvest: entry.allows_harvest,
        is_recurring: entry.is_recurring,
      });
    } else if (open) {
      reset(defaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, entry, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = {
        phase_definition_key: data.phase_definition_key,
        override_duration_days: data.override_duration_days,
        is_terminal: data.is_terminal,
        allows_harvest: data.allows_harvest,
        is_recurring: data.is_recurring,
      };
      if (isEdit && entry) {
        await phaseSequenceApi.updateSequenceEntry(sequenceKey, entry.key, payload);
        notification.success(t('pages.phaseSequences.sequenceUpdated'));
      } else {
        await phaseSequenceApi.createSequenceEntry(sequenceKey, payload);
        notification.success(t('pages.phaseSequences.sequenceUpdated'));
      }
      onSaved();
    } catch (err) {
      handleError(err, applyFieldViolation);
    } finally {
      setSaving(false);
    }
  };

  return (
    <FormDialog
      control={control}
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="phase-sequence-entry-dialog-title"
      data-testid="phase-sequence-entry-dialog"
    >
      <DialogTitle id="phase-sequence-entry-dialog-title">
        {isEdit
          ? t('pages.phaseSequences.editSequence')
          : t('pages.phaseSequences.addEntry')}
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.phaseSequences.entryDialogIntro')}
        </Typography>
        <Form onSubmit={handleSubmit(onSubmit)}>
          {/* Phase selection */}
          <Box sx={{ mt: 1 }}>
            <Controller
              name="phase_definition_key"
              control={control}
              render={({ field, fieldState: { error } }) => (
                <Autocomplete
                  options={definitionOptions}
                  loading={definitionsLoading}
                  value={
                    definitionOptions.find((d) => d.key === field.value) ?? null
                  }
                  onChange={(_e, value) => field.onChange(value?.key ?? '')}
                  getOptionLabel={(option) =>
                    localizedText(lang, { de: option.display_name_de, en: option.display_name })
                      ? `${option.name} (${localizedText(lang, { de: option.display_name_de, en: option.display_name })})`
                      : option.name
                  }
                  isOptionEqualToValue={(option, value) =>
                    option.key === value.key
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('pages.phaseSequences.selectDefinition')}
                      required
                      error={!!error}
                      helperText={error?.message}
                      slotProps={{
                        input: {
                          ...params.slotProps?.input,
                          endAdornment: (
                            <>
                              {definitionsLoading ? (
                                <CircularProgress size={20} />
                              ) : null}
                              {params.slotProps?.input?.endAdornment}
                            </>
                          ),
                        },
                      }}
                    />
                  )}
                  sx={{ mb: 2 }}
                  data-testid="form-field-phase_definition_key"
                />
              )}
            />
            {definitionsLoad.error && (
              <OptionsLoadError onRetry={definitionsLoad.reload} data-testid="sequence-definitions-load-error" />
            )}
          </Box>

          {/* Duration override */}
          <FormNumberField
            name="override_duration_days"
            control={control}
            label={t('pages.phaseSequences.overrideDuration')}
            min={1}
            step={1}
            suffix={t('common.days')}
            helperText={t('pages.phaseSequences.overrideDurationHelper')}
          />

          {/* Behavior section */}
          <Divider sx={{ my: 1.5 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.phaseSequences.sectionBehavior')}
          </Typography>
          <FormSwitchField
            name="is_terminal"
            control={control}
            label={t('pages.phaseSequences.isTerminal')}
            helperText={t('pages.phaseSequences.isTerminalHelper')}
          />
          <FormSwitchField
            name="allows_harvest"
            control={control}
            label={t('pages.phaseSequences.allowsHarvest')}
            helperText={t('pages.phaseSequences.allowsHarvestHelper')}
          />
          <FormSwitchField
            name="is_recurring"
            control={control}
            label={t('pages.phaseSequences.isRecurring')}
            helperText={t('pages.phaseSequences.isRecurringHelper')}
          />

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('common.create')}
          />
        </Form>
      </DialogContent>
    </FormDialog>
  );
}
