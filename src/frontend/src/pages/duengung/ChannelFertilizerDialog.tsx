import { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import DeleteIcon from '@mui/icons-material/Delete';
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

interface DraftDosage {
  fertilizerKey: string;
  productName: string;
  brand: string;
  mlPerLiter: string;
  optional: boolean;
}

export default function ChannelFertilizerDialog({
  open,
  onClose,
  onSave,
  fertilizers,
  existingFertilizerKeys,
  existingDosage,
}: Props) {
  const { t } = useTranslation();
  const isEdit = !!existingDosage;

  // Edit mode: single fertilizer state
  const [editMlPerLiter, setEditMlPerLiter] = useState<string>('1.0');
  const [editOptional, setEditOptional] = useState(false);

  // Add mode: multi-select state
  const [drafts, setDrafts] = useState<DraftDosage[]>([]);

  useEffect(() => {
    if (open) {
      if (existingDosage) {
        setEditMlPerLiter(existingDosage.ml_per_liter.toString());
        setEditOptional(existingDosage.optional);
        setDrafts([]);
      } else {
        setEditMlPerLiter('1.0');
        setEditOptional(false);
        setDrafts([]);
      }
    }
  }, [open, existingDosage]);

  const existingSet = useMemo(() => {
    const set = new Set(existingFertilizerKeys);
    if (existingDosage) {
      set.delete(existingDosage.fertilizer_key);
    }
    return set;
  }, [existingFertilizerKeys, existingDosage]);

  const draftKeySet = useMemo(
    () => new Set(drafts.map((d) => d.fertilizerKey)),
    [drafts],
  );

  const availableFertilizers = useMemo(
    () => fertilizers.filter((f) => !existingSet.has(f.key) && !draftKeySet.has(f.key)),
    [fertilizers, existingSet, draftKeySet],
  );

  const handleAddFertilizers = useCallback(
    (_: unknown, selected: Fertilizer[]) => {
      const newDrafts = selected
        .filter((f) => !draftKeySet.has(f.key))
        .map((f) => ({
          fertilizerKey: f.key,
          productName: f.product_name,
          brand: f.brand,
          mlPerLiter: '1.0',
          optional: false,
        }));
      setDrafts((prev) => [...prev, ...newDrafts]);
    },
    [draftKeySet],
  );

  const updateDraft = (fertKey: string, field: 'mlPerLiter' | 'optional', value: string | boolean) => {
    setDrafts((prev) =>
      prev.map((d) =>
        d.fertilizerKey === fertKey ? { ...d, [field]: value } : d,
      ),
    );
  };

  const removeDraft = (fertKey: string) => {
    setDrafts((prev) => prev.filter((d) => d.fertilizerKey !== fertKey));
  };

  const canSave = isEdit
    ? parseFloat(editMlPerLiter) > 0
    : drafts.length > 0 && drafts.every((d) => parseFloat(d.mlPerLiter) > 0);

  const handleSave = () => {
    if (isEdit && existingDosage) {
      onSave([{
        fertilizer_key: existingDosage.fertilizer_key,
        ml_per_liter: parseFloat(editMlPerLiter),
        optional: editOptional,
      }]);
    } else {
      onSave(
        drafts.map((d) => ({
          fertilizer_key: d.fertilizerKey,
          ml_per_liter: parseFloat(d.mlPerLiter),
          optional: d.optional,
        })),
      );
    }
  };

  const editFertName = useMemo(() => {
    if (!existingDosage) return '';
    const f = fertilizers.find((fert) => fert.key === existingDosage.fertilizer_key);
    return f ? `${f.product_name} (${f.brand})` : existingDosage.fertilizer_key;
  }, [existingDosage, fertilizers]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEdit
          ? t('pages.nutrientPlans.editFertilizer')
          : t('pages.nutrientPlans.addFertilizer')}
      </DialogTitle>
      <DialogContent>
        {isEdit ? (
          /* ── Edit mode: single fertilizer ─────────────────────── */
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label={t('entities.fertilizer')}
              value={editFertName}
              size="small"
              disabled
            />
            <TextField
              label={t('pages.nutrientPlans.mlPerLiter')}
              type="number"
              value={editMlPerLiter}
              onChange={(e) => setEditMlPerLiter(e.target.value)}
              size="small"
              required
              inputProps={{ min: 0.1, max: 50, step: 0.1 }}
              helperText={t('pages.nutrientPlans.mlPerLiterHelper')}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={editOptional}
                  onChange={(e) => setEditOptional(e.target.checked)}
                />
              }
              label={t('common.optional')}
            />
          </Box>
        ) : (
          /* ── Add mode: multi-select ───────────────────────────── */
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
                  placeholder={drafts.length === 0
                    ? t('pages.nutrientPlans.selectFertilizers')
                    : undefined}
                />
              )}
              isOptionEqualToValue={(option, value) => option.key === value.key}
              renderTags={() => null}
            />

            {drafts.length > 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('pages.nutrientPlans.selectedFertilizers', { count: drafts.length })}
                </Typography>
                {drafts.map((draft) => (
                  <Box key={draft.fertilizerKey}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        mb: 0.5,
                      }}
                    >
                      <Chip
                        label={`${draft.productName} (${draft.brand})`}
                        size="small"
                        variant="outlined"
                        sx={{ flexShrink: 0 }}
                      />
                      <Box sx={{ flexGrow: 1 }} />
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => removeDraft(draft.fertilizerKey)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <TextField
                        label={t('pages.nutrientPlans.mlPerLiter')}
                        type="number"
                        value={draft.mlPerLiter}
                        onChange={(e) =>
                          updateDraft(draft.fertilizerKey, 'mlPerLiter', e.target.value)
                        }
                        size="small"
                        required
                        inputProps={{ min: 0.1, max: 50, step: 0.1 }}
                        sx={{ width: 120 }}
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={draft.optional}
                            onChange={(e) =>
                              updateDraft(draft.fertilizerKey, 'optional', e.target.checked)
                            }
                            size="small"
                          />
                        }
                        label={t('common.optional')}
                      />
                    </Box>
                    <Divider sx={{ mt: 1 }} />
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button variant="contained" onClick={handleSave} disabled={!canSave}>
          {t('common.save')}
          {!isEdit && drafts.length > 1 && ` (${drafts.length})`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
