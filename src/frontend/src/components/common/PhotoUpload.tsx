import { useState, useCallback, useMemo } from 'react';
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
import AuthImage from '@/components/common/AuthImage';
import * as taskApi from '@/api/endpoints/tasks';

/** Stable default, so an omitted prop does not remount-thrash the memo below. */
const EMPTY_REFS: readonly string[] = [];

interface Props {
  taskKey: string;
  photoRefs: string[];
  /**
   * What the task already carried when the page loaded.
   *
   * Everything in `photoRefs` that is not in here was staged in this form, and only
   * a staged photo may be removed: a persisted one is the record of a completed task
   * that was reopened, where "remove" can neither destroy (that loses the record)
   * nor de-stage (`complete_task` merges `photo_refs` append-only, so it comes back).
   *
   * A **prop**, not component state. The completion form is conditionally rendered,
   * so this component unmounts on a tab switch — mount-scoped state made a staged
   * photo unremovable after one trip to the Comments tab, and it was then submitted
   * with the completion.
   *
   * Defaults to empty, which reads as "everything here was staged" — the right
   * answer for a caller that has no persisted list, and the pre-#1393 behaviour.
   */
  persistedRefs?: readonly string[];
  onChange: (refs: string[]) => void;
  disabled?: boolean;
}

export default function PhotoUpload({
  taskKey,
  photoRefs,
  persistedRefs = EMPTY_REFS,
  onChange,
  disabled,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  // `DELETE` on an attachment is the REQ-024 §1a.1 irreversibility boundary and is
  // granted to lead alone, while `CREATE` admits a grower. That governs whether the
  // stored object can be *destroyed* here — it does not govern de-staging, which is
  // what this control primarily does (#1393 review). Hiding the button from growers
  // took away their only way to drop a wrong photo before submitting, so the wrong
  // photo was submitted instead: a worse outcome than the leak being fixed.
  //: Attachment ids staged in this form — everything in `photoRefs` the task did
  //: not already carry.
  //:
  //: Derived from props rather than accumulated in state, which is what survives the
  //: unmount a tab switch causes. The previous version tracked uploads as they
  //: happened and lost the set on remount, leaving a staged photo with no remove
  //: control at all.
  //:
  //: The distinction is what keeps removal safe. A staged id is the user's own
  //: upload, so destroying it is the obvious reading of "remove". A persisted id is
  //: the record of a completed task that was reopened — `TaskDetailPage` seeds both
  //: lists from `task.photo_refs` — and there neither meaning works.
  const stagedIds = useMemo(
    () => new Set(photoRefs.filter((ref) => !persistedRefs.includes(ref))),
    [photoRefs, persistedRefs],
  );
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
          //
          // Skipped when already present: `AttachmentService.upload` deduplicates by
          // sha256 across the whole tenant and across categories, so re-uploading the
          // same bytes returns the *existing* attachment. Pushing it again would
          // duplicate a React key and repeat the entry on submit.
          if (newRefs.includes(result.attachment_id)) continue;
          newRefs.push(result.attachment_id);
          // Handed over per file, not once after the loop. Each iteration has already
          // stored an attachment server-side, so a failure on file 2 of 3 used to
          // discard file 1 from local state — leaving exactly the orphaned,
          // quota-counted photo this change exists to eliminate, and with the sweep
          // shipped disabled nothing would collect it.
          //
          // A copy, because later iterations keep mutating `newRefs` and the caller
          // stores the array it is handed. `stagedIds` derives from the list the
          // parent holds, so each handover also makes that file's remove control
          // appear — which is what the staged/persisted split means by staged.
          onChange([...newRefs]);
        }
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

      // No role branch here any more. This used to return early for a non-lead,
      // de-staging locally and issuing no request — so a grower's remove button
      // dropped the photo from the form and left the stored object behind for ever.
      // Growers are the role that completes tasks and uploads these photos, so that
      // was the leak #1393 exists to close, on its most common path, and the sweep
      // named as the backstop ships disabled.
      //
      // The server now decides per photo instead of per role: a staged upload may be
      // withdrawn by whoever made it, a photo the task already references stays
      // lead-only (REQ-024 §1a.1). A grower who somehow reaches the second case gets
      // the 404 handled below, which de-stages without claiming the bytes are gone.
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
    [taskKey, photoRefs, stagedIds, onChange, handleError],
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
                  // `uploading` too, matching the upload button above: the two
                  // handlers must stay mutually exclusive. Handing each file to the
                  // parent as it lands (rather than once after the loop) makes file
                  // 1's remove control render while file 2 is still in flight, and a
                  // click there deletes the attachment while the loop still holds
                  // `att-1` in its own `newRefs` snapshot — whose next `onChange`
                  // puts the deleted id straight back. The gallery then shows a
                  // broken image and `complete` answers 422 for an id the catalogue
                  // no longer has.
                  disabled={disabled || uploading || removingIndex !== null}
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
