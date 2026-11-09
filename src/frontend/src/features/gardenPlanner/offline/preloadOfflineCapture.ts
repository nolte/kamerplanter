/**
 * Everything an offline capture needs, loaded while the network is still there (REQ-053 WP 9.4, #2755).
 *
 * The three bufferable actions of field mode — "Done", the note, the photo — reach code in lazy chunks: the buffer's
 * IndexedDB layer (Dexie, `queueDb`) and the dialogs of the note and the photo. Offline a chunk that was never
 * loaded cannot be fetched (the worker caches lazy chunks only on first use, and without a worker nothing serves
 * them), so the first offline capture of a device failed: "Done" as an unknown error, the note as the error page.
 *
 * One place loads all of it: the bed sheet, while the buffer is usable and the device online — never every signed-in
 * page. A failed load is not remembered, so the next call (the sheet calls again after a reconnect) tries again.
 */
import { preloadWriteQueue } from './queue';

let loaded: Promise<boolean> | null = null;

async function loadAll(): Promise<boolean> {
  const [queueReady] = await Promise.all([
    preloadWriteQueue(),
    import('../care/CareLogDialog'),
    import('@/components/photos/PlantPhotoUploadDialog'),
  ]);
  return queueReady;
}

/** Resolves `true` once the buffer's code and both dialogs are in memory; `false` when a part could not load. */
export function preloadOfflineCapture(): Promise<boolean> {
  loaded ??= loadAll().then(
    (ready) => {
      if (!ready) loaded = null;
      return ready;
    },
    () => {
      loaded = null;
      return false;
    },
  );
  return loaded;
}

/** Tests only: forget a finished preload. */
export function resetOfflineCapturePreloadForTests(): void {
  loaded = null;
}
