import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import DeleteIcon from '@mui/icons-material/Delete';
import FormActions from '@/components/form/FormActions';
import FormChipInput from '@/components/form/FormChipInput';
import FormRow from '@/components/form/FormRow';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import AuthImage from '@/components/common/AuthImage';
import DiaryEnvironmentReadings from '@/components/diary/DiaryEnvironmentReadings';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import {
  DIARY_ENTRY_TYPES,
  DIARY_MAX_PHOTOS,
  createPlantDiaryEntry,
  diaryPhotoUri,
  getPlantEnvironmentPreview,
  updatePlantDiaryEntry,
} from '@/api/endpoints/diary';
import type { DiaryEntryType, PlantDiaryEntry, PlantEnvironmentPreview } from '@/api/types';
import DiaryPhotoUploadDialog from './DiaryPhotoUploadDialog';

const schema = z.object({
  entry_type: z.enum(['observation', 'problem', 'milestone', 'measurement', 'photo', 'note']),
  // Mirrors `DiaryEntryCreateRequest`: title optional (max 200), text required
  // (1..5000). Validating client-side only saves a round trip — the backend
  // enforces the same bounds and stays the authority.
  title: z.string().max(200),
  text: z.string().min(1).max(5000),
  tags: z.array(z.string()),
  measurements: z.array(
    z.object({
      name: z.string(),
      value: z.string(),
    }),
  ),
});

type FormData = z.infer<typeof schema>;

interface DiaryEntryDialogProps {
  open: boolean;
  plantInstanceKey: string;
  /** `null` creates a new entry; an entry switches the dialog into edit mode. */
  entry: PlantDiaryEntry | null;
  onClose: () => void;
  onSaved: (entry: PlantDiaryEntry) => void;
}

/**
 * Turn the free-form `measurements` object into editable rows.
 *
 * `measurements` is an open object by REQ-013 — no fixed key set — so the editor
 * is a key/value list rather than a fixed form. Values are carried as strings
 * while editing and converted back on submit.
 */
function toRows(measurements: Record<string, unknown> | null | undefined) {
  return Object.entries(measurements ?? {}).map(([name, value]) => ({
    name,
    value: value === null || value === undefined ? '' : String(value),
  }));
}

/**
 * Convert the rows back into the payload object.
 *
 * A value that parses as a finite number is sent as a number, everything else as
 * a string: `{"height_cm": 84}` is what §4.3 shows an agent receiving, and
 * `"84"` would make every consumer parse it again. Rows without a name are
 * dropped — an empty row is a half-finished edit, not a measurement.
 */
function toMeasurements(rows: FormData['measurements']): Record<string, unknown> | null {
  const result: Record<string, unknown> = {};
  for (const row of rows) {
    const name = row.name.trim();
    if (!name) continue;
    const raw = row.value.trim();
    const asNumber = Number(raw);
    result[name] = raw !== '' && Number.isFinite(asNumber) ? asNumber : raw;
  }
  return Object.keys(result).length > 0 ? result : null;
}

/**
 * REQ-050 §2.5.1 — create or edit a diary entry of one plant instance.
 *
 * Photos are uploaded immediately when picked (they become attachments in their
 * own right) and the entry then references them by id. That is why the photo
 * list is component state rather than a form field: an upload is already
 * persisted when the user cancels the dialog, and pretending otherwise by
 * keeping it "unsaved" would be a lie about what happened.
 */
export default function DiaryEntryDialog({
  open,
  plantInstanceKey,
  entry,
  onClose,
  onSaved,
}: DiaryEntryDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();

  const [saving, setSaving] = useState(false);
  const [photoRefs, setPhotoRefs] = useState<string[]>([]);
  const [uploadOpen, setUploadOpen] = useState(false);
  // REQ-013 §2.3a — the environment preview. Deliberately *not* a form field:
  // it is never sent back, and putting it in the form would make the dialog
  // "dirty" for a value the user cannot change.
  const [envPreview, setEnvPreview] = useState<PlantEnvironmentPreview | null>(null);
  const [envLoading, setEnvLoading] = useState(false);
  const [captureEnvironment, setCaptureEnvironment] = useState(true);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      entry_type: 'observation',
      title: '',
      text: '',
      tags: [],
      measurements: [],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'measurements' });

  // Load the entry (or the blank defaults) whenever the dialog opens. Resetting
  // on open rather than on close keeps a half-typed entry from flashing while
  // the dialog animates out.
  useEffect(() => {
    if (!open) return;
    reset({
      entry_type: entry?.entry_type ?? 'observation',
      title: entry?.title ?? '',
      text: entry?.text ?? '',
      tags: entry?.tags ?? [],
      measurements: toRows(entry?.measurements),
    });
    setPhotoRefs(entry?.photo_refs ?? []);
    setCaptureEnvironment(true);
    // The preview belongs to the reset, not to the fetch below: clearing it here
    // means the section never shows the previous plant's climate for a frame,
    // and it keeps the fetching effect free of synchronous state writes.
    setEnvPreview(null);
    setEnvLoading(!entry);
  }, [open, entry, reset]);

  // Load the preview only when a *new* entry is being written. Editing never
  // re-captures (the server protects the fields), so previewing there would show
  // a climate that is not going to be stored — a promise the save cannot keep.
  useEffect(() => {
    if (!open || entry) return;
    let cancelled = false;
    getPlantEnvironmentPreview(plantInstanceKey)
      .then((preview) => {
        if (!cancelled) setEnvPreview(preview);
      })
      .catch(() => {
        // A failed preview is not an error the grower has to act on: the entry
        // saves either way, and the server records honestly that the capture did
        // not get through. Surfacing a toast here would turn a non-event into an
        // interruption at the worst moment — while documenting a problem.
        if (!cancelled) setEnvPreview(null);
      })
      .finally(() => {
        if (!cancelled) setEnvLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, entry, plantInstanceKey]);

  const handlePhotoUploaded = useCallback((attachmentId: string) => {
    setPhotoRefs((prev) =>
      prev.includes(attachmentId) || prev.length >= DIARY_MAX_PHOTOS
        ? prev
        : [...prev, attachmentId],
    );
  }, []);

  const handleRemovePhoto = useCallback((attachmentId: string) => {
    setPhotoRefs((prev) => prev.filter((id) => id !== attachmentId));
  }, []);

  const onSubmit = useCallback(
    async (data: FormData) => {
      setSaving(true);
      try {
        const payload = {
          entry_type: data.entry_type as DiaryEntryType,
          title: data.title.trim() === '' ? null : data.title.trim(),
          text: data.text,
          tags: data.tags,
          measurements: toMeasurements(data.measurements),
          photo_refs: photoRefs,
        };
        const saved = entry
          ? await updatePlantDiaryEntry(plantInstanceKey, entry.key, payload)
          : await createPlantDiaryEntry(plantInstanceKey, {
              ...payload,
              // Only the *permission* to look travels. The readings are resolved
              // server-side; the client never sends them (REQ-013 §2.3a).
              capture_environment: captureEnvironment,
            });
        notification.success(entry ? t('common.saved') : t('pages.plantDiary.created'));
        onSaved(saved);
        onClose();
      } catch (err) {
        handleError(err);
      } finally {
        setSaving(false);
      }
    },
    [
      entry,
      plantInstanceKey,
      photoRefs,
      captureEnvironment,
      notification,
      t,
      onSaved,
      onClose,
      handleError,
    ],
  );

  const typeOptions = DIARY_ENTRY_TYPES.map((value) => ({
    value,
    label: t(`enums.diaryEntryType.${value}`),
  }));

  const photoLimitReached = photoRefs.length >= DIARY_MAX_PHOTOS;

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={saving ? undefined : onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="diary-entry-dialog-title"
      data-testid="diary-entry-dialog"
    >
      <DialogTitle id="diary-entry-dialog-title">
        {entry ? t('pages.plantDiary.editEntry') : t('pages.plantDiary.createEntry')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantDiary.formIntro')}
        </Typography>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <FormRow>
            <FormSelectField
              name="entry_type"
              control={control}
              label={t('pages.plantDiary.entryType')}
              options={typeOptions}
            />
            <FormTextField
              name="title"
              control={control}
              label={t('pages.plantDiary.title')}
              helperText={t('pages.plantDiary.titleHint')}
            />
          </FormRow>

          <FormTextField
            name="text"
            control={control}
            label={t('pages.plantDiary.text')}
            helperText={t('pages.plantDiary.textHint')}
            required
            multiline
            minRows={4}
            maxRows={12}
          />

          <FormChipInput
            name="tags"
            control={control}
            label={t('pages.plantDiary.tags')}
            helperText={t('pages.plantDiary.tagsHint')}
          />

          {/* ── Measurements (open key/value set, REQ-013) ─────────── */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5, mt: 2 }}>
            {t('pages.plantDiary.measurements')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.plantDiary.measurementsHint')}
          </Typography>
          {fields.map((field, index) => (
            <Box
              key={field.id}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', mb: 1 }}
              data-testid="diary-measurement-row"
            >
              <FormTextField
                name={`measurements.${index}.name`}
                control={control}
                label={t('pages.plantDiary.measurementName')}
              />
              <FormTextField
                name={`measurements.${index}.value`}
                control={control}
                label={t('pages.plantDiary.measurementValue')}
              />
              <IconButton
                onClick={() => remove(index)}
                aria-label={t('pages.plantDiary.removeMeasurement')}
                sx={{ mt: 1, minWidth: 44, minHeight: 44 }}
                data-testid="diary-measurement-remove"
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          ))}
          <Button
            startIcon={<AddIcon />}
            onClick={() => append({ name: '', value: '' })}
            sx={{ minHeight: 44 }}
            data-testid="diary-measurement-add"
          >
            {t('pages.plantDiary.addMeasurement')}
          </Button>

          {/* ── Environment snapshot (REQ-013 §2.3a) ───────────────── */}
          {/* New entries only: an edit never re-captures, so showing a preview
              there would advertise a value the save is not going to store. */}
          {!entry && (
            <Box sx={{ mt: 2 }} data-testid="diary-environment-section">
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                {t('pages.plantDiary.environment.sectionTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t('pages.plantDiary.environment.sectionHint')}
              </Typography>

              {envLoading && (
                <Box
                  sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}
                  data-testid="diary-environment-loading"
                >
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.plantDiary.environment.loading')}
                  </Typography>
                </Box>
              )}

              {!envLoading && envPreview && envPreview.readings.length > 0 && (
                <DiaryEnvironmentReadings
                  readings={envPreview.readings}
                  testIdPrefix="diary-environment-preview"
                />
              )}

              {/* An empty preview says *which* empty it is. "No sensor covers
                  this plant" is a hint to attach one; "sensors unreachable" is
                  a hint to check Home Assistant. One message for both would be
                  useless for either. */}
              {!envLoading && (!envPreview || envPreview.readings.length === 0) && (
                <Alert severity="info" icon={false} data-testid="diary-environment-empty">
                  {t(
                    `pages.plantDiary.environment.empty.${envPreview?.environment_status ?? 'unavailable'}`,
                  )}
                </Alert>
              )}

              {/* The opt-out. Offered unconditionally, including when the
                  preview is empty: the capture runs again at save time and may
                  well find something the preview did not. */}
              <FormControlLabel
                sx={{ mt: 1 }}
                control={
                  <Checkbox
                    checked={captureEnvironment}
                    onChange={(event) => setCaptureEnvironment(event.target.checked)}
                    slotProps={{
                      input: { 'aria-label': t('pages.plantDiary.environment.capture') },
                    }}
                    data-testid="diary-environment-capture-toggle"
                  />
                }
                label={t('pages.plantDiary.environment.capture')}
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                {t('pages.plantDiary.environment.captureHint')}
              </Typography>
            </Box>
          )}

          {/* ── Photos (max 5) ─────────────────────────────────────── */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5, mt: 2 }}>
            {t('pages.plantDiary.photos.sectionTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.plantDiary.photos.sectionHint', { max: DIARY_MAX_PHOTOS })}
          </Typography>
          {photoRefs.length > 0 && (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: 'repeat(3, 1fr)',
                  sm: 'repeat(5, 1fr)',
                },
                gap: 1,
                mb: 1,
              }}
              data-testid="diary-entry-photo-editor"
            >
              {photoRefs.map((attachmentId) => (
                <Card key={attachmentId} variant="outlined" sx={{ position: 'relative' }}>
                  <AuthImage
                    uri={diaryPhotoUri(attachmentId, 512)}
                    alt={t('pages.plantDiary.photos.thumbAlt')}
                    sx={{ width: '100%', aspectRatio: '1 / 1', bgcolor: 'action.hover' }}
                    data-testid="diary-entry-photo-preview"
                  />
                  <Tooltip title={t('pages.plantDiary.photos.remove')}>
                    <IconButton
                      size="small"
                      onClick={() => handleRemovePhoto(attachmentId)}
                      aria-label={t('pages.plantDiary.photos.remove')}
                      sx={{
                        position: 'absolute',
                        top: 2,
                        right: 2,
                        bgcolor: 'background.paper',
                        '&:hover': { bgcolor: 'background.paper' },
                      }}
                      data-testid="diary-entry-photo-remove"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Card>
              ))}
            </Box>
          )}
          <Button
            startIcon={<AddPhotoAlternateIcon />}
            onClick={() => setUploadOpen(true)}
            disabled={photoLimitReached}
            sx={{ minHeight: 44 }}
            data-testid="diary-add-photo"
          >
            {t('pages.plantDiary.photos.add')}
          </Button>
          {photoLimitReached && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {t('pages.plantDiary.photos.limitReached', { max: DIARY_MAX_PHOTOS })}
            </Typography>
          )}

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={entry ? t('common.save') : t('common.create')}
          />
        </form>
      </DialogContent>

      <UnsavedChangesGuard dirty={open && isDirty && !saving} />

      <DiaryPhotoUploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={handlePhotoUploaded}
      />
    </Dialog>
  );
}
