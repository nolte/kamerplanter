import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import CloseIcon from '@mui/icons-material/Close';
import SaveIcon from '@mui/icons-material/Save';
import { updatePhotoMetadata, type PlantPhoto } from '@/api/endpoints/plantPhotos';
import { isApiError } from '@/api/errors';

/** Mirrors the backend caption bound (REQ-034 §2.1 v1.2). */
const CAPTION_MAX_LENGTH = 500;

interface PlantPhotoEditDialogProps {
  /** The photo to edit, or `null` when the dialog is closed. */
  photo: PlantPhoto | null;
  plantInstanceKey: string;
  onClose: () => void;
  /** Called with the updated photo after a successful save. */
  onSaved: (updated: PlantPhoto) => void;
}

/** Today's date as `YYYY-MM-DD` for the native date input's `max` (no future). */
function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * REQ-034 §2.1 v1.2 — edit a gallery photo's caption and capture date.
 *
 * Caption is a multiline field with a live 500-character counter; the capture
 * date is a native date input that defaults to the photo's current
 * `taken_on ?? created_at` and is capped at today (no future date — the backend
 * enforces this too with a 422). Only the changed fields are PATCHed (true
 * partial update): an emptied caption is sent as `null` to clear it.
 *
 * A11y (UI-NFR-002 / UI-NFR-008):
 * - the caption field receives focus on open so keyboard users land on the
 *   primary input;
 * - the error Alert uses `role="alert"` (MUI `severity="error"`) so it is
 *   announced without manual navigation;
 * - the dialog has an accessible title via `aria-labelledby`.
 */
export default function PlantPhotoEditDialog({
  photo,
  plantInstanceKey,
  onClose,
  onSaved,
}: PlantPhotoEditDialogProps) {
  const { t } = useTranslation();

  const [caption, setCaption] = useState('');
  const [takenOn, setTakenOn] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const captionRef = useRef<HTMLInputElement>(null);

  // Seed the form from the photo whenever the dialog (re)opens for a photo.
  // The capture date defaults to taken_on, falling back to the upload date.
  useEffect(() => {
    if (!photo) return;
    setError(null);
    setSaving(false);
    setCaption(photo.caption ?? '');
    const initialDate = (photo.taken_on ?? photo.created_at ?? '').slice(0, 10);
    setTakenOn(initialDate);
    const id = setTimeout(() => captionRef.current?.focus(), 50);
    return () => clearTimeout(id);
  }, [photo]);

  const maxDate = useMemo(() => todayIso(), []);
  const tooLong = caption.length > CAPTION_MAX_LENGTH;

  const handleSave = useCallback(async () => {
    if (!photo || tooLong) return;
    setSaving(true);
    setError(null);

    // Build a minimal PATCH body: only send fields the user actually changed.
    // An emptied caption is an explicit clear (null); an empty date is a clear
    // (fall back to created_at) — both distinct from "not provided".
    const body: { caption?: string | null; taken_on?: string | null } = {};
    const nextCaption = caption.trim().length === 0 ? null : caption;
    if (nextCaption !== (photo.caption ?? null)) {
      body.caption = nextCaption;
    }
    const nextTakenOn = takenOn.length === 0 ? null : takenOn;
    const currentTakenOn = photo.taken_on ?? null;
    if (nextTakenOn !== currentTakenOn) {
      body.taken_on = nextTakenOn;
    }

    // Nothing changed — close without a needless request.
    if (Object.keys(body).length === 0) {
      onClose();
      return;
    }

    try {
      const updated = await updatePhotoMetadata(plantInstanceKey, photo.attachment_id, body);
      onSaved(updated);
      onClose();
    } catch (err) {
      if (isApiError(err) && err.statusCode === 422) {
        setError(t('pages.plantPhotos.metadataInvalid'));
      } else if (isApiError(err) && err.statusCode === 403) {
        setError(t('pages.plantPhotos.editForbidden'));
      } else {
        setError(t('pages.plantPhotos.metadataError'));
      }
      setSaving(false);
    }
  }, [photo, tooLong, caption, takenOn, plantInstanceKey, onSaved, onClose, t]);

  return (
    <Dialog
      open={photo !== null}
      onClose={saving ? undefined : onClose}
      maxWidth="sm"
      fullWidth
      data-testid="plant-photo-edit-dialog"
      aria-labelledby="plant-photo-edit-title"
    >
      <DialogTitle id="plant-photo-edit-title" sx={{ pr: 6 }}>
        {t('pages.plantPhotos.editTitle')}
        <IconButton
          onClick={onClose}
          disabled={saving}
          aria-label={t('common.close')}
          sx={{ position: 'absolute', right: 8, top: 8 }}
          data-testid="plant-photo-edit-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            inputRef={captionRef}
            label={t('pages.plantPhotos.caption')}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            multiline
            minRows={2}
            maxRows={6}
            fullWidth
            disabled={saving}
            error={tooLong}
            helperText={
              tooLong
                ? t('pages.plantPhotos.captionTooLong', { max: CAPTION_MAX_LENGTH })
                : `${caption.length} / ${CAPTION_MAX_LENGTH}`
            }
            slotProps={{ htmlInput: { 'data-testid': 'plant-photo-caption-input' } }}
          />

          <TextField
            label={t('pages.plantPhotos.takenOn')}
            type="date"
            value={takenOn}
            onChange={(e) => setTakenOn(e.target.value)}
            fullWidth
            disabled={saving}
            helperText={t('pages.plantPhotos.takenOnHelper')}
            slotProps={{
              inputLabel: { shrink: true },
              htmlInput: { max: maxDate, 'data-testid': 'plant-photo-takenon-input' },
            }}
          />

          {error && (
            <Alert severity="error" data-testid="plant-photo-edit-error">
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 2, py: 1.5, gap: 1 }}>
        <Button onClick={onClose} disabled={saving} data-testid="plant-photo-edit-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving || tooLong}
          startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
          /* Minimum 44px touch target on mobile (UI-NFR-001 R-008) */
          sx={{ minHeight: 44 }}
          data-testid="plant-photo-edit-save"
        >
          {saving ? t('pages.plantPhotos.saving') : t('common.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
