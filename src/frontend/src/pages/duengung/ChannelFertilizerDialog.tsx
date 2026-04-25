import { useEffect, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import DeleteIcon from '@mui/icons-material/Delete';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import type { Fertilizer, FertilizerDosage } from '@/api/types';

export interface DosageEntry {
  fertilizer_key: string;
  ml_per_liter: number;
  optional: boolean;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (data: DosageEntry[]) => void;
  fertilizers: Fertilizer[];
  existingFertilizerKeys: string[];
  existingDosage?: FertilizerDosage | null;
}

// ── Edit-mode schema (single dosage) ─────────────────────────────
const editSchema = z.object({
  ml_per_liter: z.number().gt(0).max(50),
  optional: z.boolean(),
});
type EditFormData = z.infer<typeof editSchema>;

// ── Add-mode schema (draft list) ─────────────────────────────────
const draftSchema = z.object({
  fertilizer_key: z.string().min(1),
  product_name: z.string(),
  brand: z.string(),
  ml_per_liter: z.number().gt(0).max(50),
  optional: z.boolean(),
});
const addSchema = z.object({
  drafts: z.array(draftSchema).min(1),
});
type AddFormData = z.infer<typeof addSchema>;

export default function ChannelFertilizerDialog({
  open,
  onClose,
  onSave,
  fertilizers,
  existingFertilizerKeys,
  existingDosage,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const isEdit = !!existingDosage;

  return isEdit ? (
    <EditDialog
      open={open}
      onClose={onClose}
      onSave={onSave}
      fullScreen={fullScreen}
      t={t}
      fertilizers={fertilizers}
      existingDosage={existingDosage}
    />
  ) : (
    <AddDialog
      open={open}
      onClose={onClose}
      onSave={onSave}
      fullScreen={fullScreen}
      t={t}
      fertilizers={fertilizers}
      existingFertilizerKeys={existingFertilizerKeys}
    />
  );
}

// ─────────────────────────────────────────────────────────────────
// Edit mode — single fertilizer dosage
// ─────────────────────────────────────────────────────────────────

interface EditDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: DosageEntry[]) => void;
  fullScreen: boolean;
  t: (key: string) => string;
  fertilizers: Fertilizer[];
  existingDosage: FertilizerDosage;
}

function EditDialog({
  open,
  onClose,
  onSave,
  fullScreen,
  t,
  fertilizers,
  existingDosage,
}: EditDialogProps) {
  const { control, handleSubmit, reset, formState } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      ml_per_liter: existingDosage.ml_per_liter,
      optional: existingDosage.optional,
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        ml_per_liter: existingDosage.ml_per_liter,
        optional: existingDosage.optional,
      });
    }
  }, [open, existingDosage, reset]);

  const editFertName = useMemo(() => {
    const f = fertilizers.find((fert) => fert.key === existingDosage.fertilizer_key);
    return f ? `${f.product_name} (${f.brand})` : existingDosage.fertilizer_key;
  }, [existingDosage, fertilizers]);

  const onSubmit = (data: EditFormData) => {
    onSave([
      {
        fertilizer_key: existingDosage.fertilizer_key,
        ml_per_liter: data.ml_per_liter,
        optional: data.optional,
      },
    ]);
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="channel-fertilizer-dialog-title"
      data-testid="channel-fertilizer-dialog"
    >
      <DialogTitle id="channel-fertilizer-dialog-title">
        {t('pages.nutrientPlans.editFertilizer')}
      </DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label={t('entities.fertilizer')}
              value={editFertName}
              size="small"
              disabled
            />
            <FormNumberField
              name="ml_per_liter"
              control={control}
              label={t('pages.nutrientPlans.mlPerLiter')}
              required
              min={0.1}
              max={50}
              step={0.1}
              inputMode="decimal"
              helperText={t('pages.nutrientPlans.mlPerLiterHelper')}
            />
            <FormSwitchField
              name="optional"
              control={control}
              label={t('common.optional')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>{t('common.cancel')}</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={formState.isSubmitting}
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────
// Add mode — multi-select with draft list
// ─────────────────────────────────────────────────────────────────

interface AddDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: DosageEntry[]) => void;
  fullScreen: boolean;
  t: (key: string, options?: Record<string, unknown>) => string;
  fertilizers: Fertilizer[];
  existingFertilizerKeys: string[];
}

function AddDialog({
  open,
  onClose,
  onSave,
  fullScreen,
  t,
  fertilizers,
  existingFertilizerKeys,
}: AddDialogProps) {
  const { control, handleSubmit, reset, formState } = useForm<AddFormData>({
    resolver: zodResolver(addSchema),
    defaultValues: { drafts: [] },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'drafts',
  });

  // Watch drafts so the save-button label can show the count.
  const draftsWatched = useWatch({ control, name: 'drafts' });
  const draftCount = draftsWatched?.length ?? 0;

  useEffect(() => {
    if (open) {
      reset({ drafts: [] });
    }
  }, [open, reset]);

  const existingSet = useMemo(
    () => new Set(existingFertilizerKeys),
    [existingFertilizerKeys],
  );

  const draftKeySet = useMemo(
    () => new Set((draftsWatched ?? []).map((d) => d.fertilizer_key)),
    [draftsWatched],
  );

  const availableFertilizers = useMemo(
    () =>
      fertilizers.filter(
        (f) => !existingSet.has(f.key) && !draftKeySet.has(f.key),
      ),
    [fertilizers, existingSet, draftKeySet],
  );

  const handleAddFertilizers = useCallback(
    (_: unknown, selected: Fertilizer[]) => {
      const newDrafts = selected
        .filter((f) => !draftKeySet.has(f.key))
        .map((f) => ({
          fertilizer_key: f.key,
          product_name: f.product_name,
          brand: f.brand,
          ml_per_liter: 1.0,
          optional: false,
        }));
      newDrafts.forEach((d) => append(d));
    },
    [draftKeySet, append],
  );

  const onSubmit = (data: AddFormData) => {
    onSave(
      data.drafts.map((d) => ({
        fertilizer_key: d.fertilizer_key,
        ml_per_liter: d.ml_per_liter,
        optional: d.optional,
      })),
    );
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="channel-fertilizer-dialog-title"
      data-testid="channel-fertilizer-dialog"
    >
      <DialogTitle id="channel-fertilizer-dialog-title">
        {t('pages.nutrientPlans.addFertilizer')}
      </DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Autocomplete
              multiple
              options={availableFertilizers}
              value={[]}
              onChange={handleAddFertilizers}
              getOptionLabel={(f) => `${f.product_name} (${f.brand})`}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('entities.fertilizer')}
                  size="small"
                  placeholder={
                    draftCount === 0
                      ? t('pages.nutrientPlans.selectFertilizers')
                      : undefined
                  }
                />
              )}
              isOptionEqualToValue={(option, value) => option.key === value.key}
              renderValue={() => null}
            />

            {fields.length > 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('pages.nutrientPlans.selectedFertilizers', {
                    count: fields.length,
                  })}
                </Typography>
                {fields.map((field, index) => (
                  <Box key={field.id}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        mb: 0.5,
                      }}
                    >
                      <Chip
                        label={`${field.product_name} (${field.brand})`}
                        size="small"
                        variant="outlined"
                        sx={{ flexShrink: 0 }}
                      />
                      <Box sx={{ flexGrow: 1 }} />
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => remove(index)}
                        aria-label={t('common.delete')}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Box sx={{ width: 140 }}>
                        <FormNumberField
                          name={`drafts.${index}.ml_per_liter`}
                          control={control}
                          label={t('pages.nutrientPlans.mlPerLiter')}
                          required
                          min={0.1}
                          max={50}
                          step={0.1}
                          inputMode="decimal"
                        />
                      </Box>
                      <FormSwitchField
                        name={`drafts.${index}.optional`}
                        control={control}
                        label={t('common.optional')}
                      />
                    </Box>
                    <Divider sx={{ mt: 1 }} />
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>{t('common.cancel')}</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={formState.isSubmitting || draftCount === 0}
          >
            {t('common.save')}
            {draftCount > 1 && ` (${draftCount})`}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
