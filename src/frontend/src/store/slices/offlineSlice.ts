import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

/**
 * The offline state of the app (UI-NFR-012 R-052, REQ-053 WP 9.4): connectivity, what the offline write buffer
 * holds, the progress of a running sync and the time of the last one.
 *
 * Deliberately WITHOUT a generic Axios interceptor (operator question 4 of wave 9, #2759, replacing R-053 for this
 * wave): only "Done", a note and a photo in field mode are ever buffered, by the field sheet itself. The buffer's
 * entries live in IndexedDB (`features/gardenPlanner/offline/queue.ts`); this slice carries counts only — no
 * entry, no text, no photo — and is filled by the sync host. A session end resets it with every slice.
 */
export interface OfflineQueueCounts {
  /** Waiting for a sync (pending or being sent). */
  pending: number;
  /** Five attempts failed or the server refused (R-027). */
  failed: number;
  /** A conflict waits for keep/discard, or was kept on the device. */
  conflict: number;
  /** Every entry of the device (the R-019 capacity counts them all). */
  total: number;
}

export interface OfflineState {
  online: boolean;
  counts: OfflineQueueCounts;
  /** The running sync: `done` of `total` handled (R-024), or `null`. */
  progress: { done: number; total: number } | null;
  /** Epoch ms of the last sync that sent at least one entry (R-025), or `null`. */
  lastSyncAt: number | null;
}

const initialState: OfflineState = {
  online: true,
  counts: { pending: 0, failed: 0, conflict: 0, total: 0 },
  progress: null,
  lastSyncAt: null,
};

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    connectivityChanged(state, action: PayloadAction<boolean>) {
      state.online = action.payload;
    },
    queueCountsChanged(state, action: PayloadAction<OfflineQueueCounts>) {
      state.counts = action.payload;
    },
    syncProgressed(state, action: PayloadAction<{ done: number; total: number } | null>) {
      state.progress = action.payload;
    },
    syncSucceeded(state, action: PayloadAction<number>) {
      state.lastSyncAt = action.payload;
    },
  },
});

export const { connectivityChanged, queueCountsChanged, syncProgressed, syncSucceeded } = offlineSlice.actions;

/** Entries of the active scope not yet at the server. */
export function unsyncedCount(counts: OfflineQueueCounts): number {
  return counts.pending + counts.failed + counts.conflict;
}

export default offlineSlice.reducer;
