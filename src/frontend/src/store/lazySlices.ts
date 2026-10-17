/**
 * Registry for slices that are injected into the root reducer when their route loads.
 *
 * A lazy route chunk must not import `rootReducer.ts` itself: that module pulls every slice, and a
 * module graph shared between the entry and a dynamic chunk makes the bundler split the slices into
 * dozens of small preloaded chunks (measured: 12 -> 39 initial chunks, +1.3 KB gzip). This module
 * imports nothing, so sharing it costs a few bytes. `rootReducer.ts` hands over its reducer once
 * (`connectLazySlices`); a slice registered earlier is injected at that moment.
 */

/** The part of a Redux Toolkit slice this registry needs. */
export interface InjectableSlice<Target> {
  injectInto: (target: Target) => unknown;
}

let target: unknown = null;
const waiting: InjectableSlice<never>[] = [];

/** Called by `rootReducer.ts` with the combined reducer that accepts injected slices. */
export function connectLazySlices<Target>(reducer: Target): void {
  target = reducer;
  for (const slice of waiting.splice(0)) (slice as InjectableSlice<Target>).injectInto(reducer);
}

/** Inject `slice` into the root reducer; idempotent. Safe to call before the store module ran. */
export function registerLazySlice<Target>(slice: InjectableSlice<Target>): void {
  if (target === null) {
    waiting.push(slice as InjectableSlice<never>);
    return;
  }
  slice.injectInto(target as Target);
}
