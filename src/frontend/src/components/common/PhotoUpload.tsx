import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import AuthImage from '@/components/common/AuthImage';
import * as taskApi from '@/api/endpoints/tasks';

interface Props {
  taskKey: string;
  photoRefs: string[];
  onChange: (refs: string[]) => void;
  disabled?: boolean;
}

export default function PhotoUpload({ taskKey, photoRefs, onChange, disabled }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  // `DELETE` on an attachment is the REQ-024 §1a.1 irreversibility boundary and is
  // granted to lead alone, while `CREATE` admits a grower too. So a grower can
  // upload a photo here and cannot remove it, and showing the button anyway would
  // make it a control that answers a refusal (#1261) — the very thing this change
  // set out to fix. An upload a grower abandons is collected by the nightly orphan
  // sweep instead (#1393).
  const { canDelete } = useTenantPermissions();
  const [uploading, setUploading] = useState(false);
  //: Which row is mid-delete, so its button can show it and not be clicked twice.
  const [removingIndex, setRemovingIndex] = useState<number | null>(null);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      setUploading(true);
      const newRefs = [...photoRefs];
      try {
        for (const file of Array.from(files)) {
          const result = await taskApi.uploadTaskPhoto(taskKey, file);
          // The bare attachment id, never `result.uri`: `photo_refs` is a list
          // of attachment ids (NFR-013 §2.2 / AC-09), and a stored URI would
          // bake in the tenant slug — which a rename re-derives (#1339 review).
          newRefs.push(result.attachment_id);
        }
        onChange(newRefs);
        notification.success(t('pages.tasks.photoUploaded'));
      } catch (err) {
        handleError(err);
      } finally {
        setUploading(false);
        e.target.value = '';
      }
    },
    [taskKey, photoRefs, onChange, notification, handleError, t],
  );

  /**
   * Remove a staged photo — from the server as well as from local state (#1393).
   *
   * This used to filter the local array and issue no request, because there was no
   * route to issue one to. The stored object stayed, counting against the tenant's
   * storage quota, with no surface in the product that reached it for the `task`
   * category: a control that looked like a delete and was not.
   *
   * The local state is updated **after** the request succeeds, not before. An
   * optimistic removal would leave the user believing a photo is gone that is
   * still there and still counted, which is the state this change exists to end.
   * On failure the list is untouched and the error surfaces.
   */
  const handleRemove = useCallback(
    async (index: number) => {
      const attachmentId = photoRefs[index];
      if (attachmentId === undefined) return;

      setRemovingIndex(index);
      try {
        await taskApi.deleteTaskPhoto(taskKey, attachmentId);
        onChange(photoRefs.filter((_, i) => i !== index));
      } catch (err) {
        handleError(err);
      } finally {
        setRemovingIndex(null);
      }
    },
    [taskKey, photoRefs, onChange, handleError],
  );

  return (
    <Box data-testid="photo-upload">
      <Button
        component="label"
        variant="outlined"
        startIcon={uploading ? <CircularProgress size={16} /> : <AddAPhotoIcon />}
        disabled={disabled || uploading}
        sx={{ mb: 1 }}
      >
        {uploading ? t('pages.tasks.photoUploading') : t('pages.tasks.photoUpload')}
        <input
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={handleFileChange}
        />
      </Button>

      {photoRefs.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
          {photoRefs.map((ref, i) => (
            <Box
              key={ref}
              sx={{
                position: 'relative',
                width: 80,
                height: 80,
                borderRadius: 1,
                overflow: 'hidden',
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <AuthImage
                uri={taskApi.taskPhotoUri(ref)}
                alt={t('pages.tasks.photoAlt', { index: i + 1 })}
                data-testid={`photo-preview-${i}`}
              />
              {canDelete && (
                <IconButton
                  size="small"
                  onClick={() => void handleRemove(i)}
                  disabled={disabled || removingIndex !== null}
                  aria-label={t('pages.tasks.photoRemove', { index: i + 1 })}
                  data-testid={`photo-remove-${i}`}
                  sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    bgcolor: 'background.paper',
                    '&:hover': { bgcolor: 'error.light', color: 'error.contrastText' },
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
          ))}
        </Box>
      )}

      {photoRefs.length === 0 && (
        <Typography variant="caption" color="text.secondary">
          {t('pages.tasks.noPhotos')}
        </Typography>
      )}
    </Box>
  );
}
