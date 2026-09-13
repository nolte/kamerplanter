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
import { ApiError } from '@/api/errors';
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
  // granted to lead alone, while `CREATE` admits a grower. That governs whether the
  // stored object can be *destroyed* here — it does not govern de-staging, which is
  // what this control primarily does (#1393 review). Hiding the button from growers
  // took away their only way to drop a wrong photo before submitting, so the wrong
  // photo was submitted instead: a worse outcome than the leak being fixed.
  const { canDelete } = useTenantPermissions();
  //: Attachment ids uploaded in *this* session, i.e. not yet part of the task's
  //: persisted `photo_refs`.
  //:
  //: The distinction is what keeps removal safe. A staged id is the user's own
  //: upload from seconds ago, so destroying it is the obvious reading of "remove".
  //: A persisted id is the photographic record of a completed task that was
  //: reopened — `TaskDetailPage` seeds `photoRefs` from `task.photo_refs` — and
  //: there "remove" can only mean "don't submit this one", never "destroy the
  //: documentation". Treating both alike deleted a completion record on a click
  //: the user could reasonably read as de-staging.
  const [stagedIds, setStagedIds] = useState<ReadonlySet<string>>(() => new Set());
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
        //: Ids this upload round produced that were not already in the list.
        //:
        //: `AttachmentService.upload` **deduplicates by sha256** across the whole
        //: tenant and across categories (`attachment_service.py`), so uploading the
        //: same bytes again returns the *existing* attachment — which may already be
        //: in `photoRefs`, may belong to another task, or may be a plant-gallery
        //: photo. Two things follow, and the first version got both wrong:
        //:
        //: - pushing the id unconditionally duplicates it in the list (duplicate
        //:   React keys, and a `photo_refs` entry repeated on submit);
        //: - marking `newRefs.slice(photoRefs.length)` as staged marks a **persisted**
        //:   id as staged, which puts the destroy control back on a reopened task's
        //:   completion photo — the exact thing that control was withdrawn from.
        const freshlyStaged: string[] = [];
        for (const file of Array.from(files)) {
          const result = await taskApi.uploadTaskPhoto(taskKey, file);
          // The bare attachment id, never `result.uri`: `photo_refs` is a list
          // of attachment ids (NFR-013 §2.2 / AC-09), and a stored URI would
          // bake in the tenant slug — which a rename re-derives (#1339 review).
          if (newRefs.includes(result.attachment_id)) continue;
          newRefs.push(result.attachment_id);
          freshlyStaged.push(result.attachment_id);
        }
        setStagedIds((current) => {
          const next = new Set(current);
          for (const ref of freshlyStaged) next.add(ref);
          return next;
        });
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
   * Remove a photo from the list, and destroy it only when that is what remove means.
   *
   * Before #1393 this filtered the local array and issued no request, because no
   * route existed to issue one to — so the stored object stayed, counting against
   * the tenant's storage quota with no surface that reached it for the `task`
   * category.
   *
   * Deleting unconditionally was the over-correction, and review caught two ways it
   * hurt:
   *
   * - a reopened task's completion photos are seeded into `photoRefs` from the
   *   persisted `task.photo_refs`, so one click destroyed documentation;
   * - hiding the control from growers (who may not `DELETE`) removed their only way
   *   to drop a wrong photo before submitting it.
   *
   * So: a staged photo can be removed — destroyed server-side when the caller may,
   * de-staged otherwise, with the nightly sweep collecting what a grower leaves
   * behind. A photo the task already carries offers no remove control at all, and
   * that is the honest answer rather than a cheap one: **neither meaning works for
   * it.** Destroying it loses the record of a completion; de-staging it does
   * nothing, because `TaskService.complete_task` merges `photo_refs` append-only and
   * never prunes — the photo would silently come back on the next completion, which
   * is worse than no control.
   *
   * The list is updated **after** the request, never optimistically: a user told a
   * photo is gone while it is still stored and still counted is the state this
   * change set out to end.
   */
  const handleRemove = useCallback(
    async (index: number) => {
      const attachmentId = photoRefs[index];
      if (attachmentId === undefined) return;
      // Unreachable from the UI — the control is not rendered for a persisted photo
      // — and kept as a guard because the alternative is a silent no-op that looks
      // like it worked.
      if (!stagedIds.has(attachmentId)) return;

      if (!canDelete) {
        onChange(photoRefs.filter((_, i) => i !== index));
        return;
      }

      setRemovingIndex(index);
      try {
        await taskApi.deleteTaskPhoto(taskKey, attachmentId);
        onChange(photoRefs.filter((_, i) => i !== index));
      } catch (err) {
        // A 404 means the server will not destroy this one — it is gone already, or
        // it is not a task photo at all. The latter is reachable: uploads are
        // deduplicated by sha256 across categories, so staging a file whose bytes
        // already exist as a plant-gallery photo hands back *that* attachment, and
        // the route rightly refuses to destroy it through a task endpoint.
        //
        // De-stage anyway. The user's intent — "not this one" — is honoured, the
        // photo stays where it belongs, and leaving the entry in the list instead
        // would give them a control that can never do anything.
        //
        // Every other failure keeps the photo: it may well still be stored and still
        // linked, and telling someone it is gone when it is not is the state this
        // whole change set out to end.
        if (err instanceof ApiError && err.statusCode === 404) {
          onChange(photoRefs.filter((_, i) => i !== index));
        } else {
          handleError(err);
        }
      } finally {
        setRemovingIndex(null);
      }
    },
    [taskKey, photoRefs, stagedIds, canDelete, onChange, handleError],
  );

  return (
    <Box data-testid="photo-upload">
      <Button
        component="label"
        variant="outlined"
        startIcon={uploading ? <CircularProgress size={16} /> : <AddAPhotoIcon />}
        // Also blocked while a removal is in flight: both handlers snapshot
            // `photoRefs` and call `onChange` with their own copy, so overlapping
            // them drops the fresh upload or re-adds the deleted id (#1393 review).
            disabled={disabled || uploading || removingIndex !== null}
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
              {stagedIds.has(ref) && (
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
