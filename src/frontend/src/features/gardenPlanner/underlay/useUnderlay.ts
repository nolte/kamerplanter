import { useCallback, useEffect, useMemo, useState } from 'react';
import type { PlanModel } from '../model/planModel';
import type { PlanUnderlay } from '../model/types';
import type { UnderlayRenderEntry } from '../renderer/types';
import { fetchUnderlayBlob } from './underlayApi';

interface LoadedImage {
  attachmentKey: string;
  href: string;
  widthPx: number;
  heightPx: number;
}

/** Decode a blob far enough to learn its natural size; the URL stays valid until the caller revokes it. */
function measure(href: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error('underlay image cannot be decoded'));
    image.src = href;
  });
}

/**
 * The underlay of the plan (REQ-053 GP-FR-033): the stored value (what every member sees), the local change after
 * this user saved or removed it, and - only while the layer is visible - the picture as a `blob:` URL with its size.
 *
 * The change is local state rather than part of the plan model on purpose: the picture is presentation, it is
 * written by its own request outside the plan revision, and it has neither undo nor a save bar. A reload of the
 * plan brings the stored value back (`base` changes, the local change no longer applies).
 */
export function useUnderlay(plan: PlanModel, visible: boolean) {
  const base = plan.settings?.underlay ?? null;
  const [changed, setChanged] = useState<{ base: PlanUnderlay | null; value: PlanUnderlay | null } | null>(null);
  const underlay = changed !== null && changed.base === base ? changed.value : base;
  const set = useCallback((value: PlanUnderlay | null) => setChanged({ base, value }), [base]);

  const [loaded, setLoaded] = useState<LoadedImage | null>(null);
  const attachmentKey = underlay?.attachment_key ?? null;
  const wanted = visible && attachmentKey !== null;
  useEffect(() => {
    if (!wanted || attachmentKey === null) return undefined;
    const abort = new AbortController();
    let href: string | null = null;
    fetchUnderlayBlob(attachmentKey, abort.signal)
      .then(async (blob) => {
        // Nothing is created for a request that was already given up: no URL, nothing to revoke.
        if (abort.signal.aborted) return;
        href = URL.createObjectURL(blob);
        const size = await measure(href);
        if (abort.signal.aborted) return;
        setLoaded({ attachmentKey, href, widthPx: size.width, heightPx: size.height });
      })
      .catch(() => {
        // The picture is an enhancement of the plan: a failed read leaves the plan as it is.
        if (!abort.signal.aborted) setLoaded(null);
      });
    return () => {
      abort.abort();
      if (href !== null) URL.revokeObjectURL(href);
      // The URL is revoked: the state must not keep naming it (hide, then show, would draw a dead image).
      setLoaded(null);
    };
  }, [wanted, attachmentKey]);

  const entry = useMemo<UnderlayRenderEntry | undefined>(
    () =>
      wanted && underlay !== null && loaded?.attachmentKey === attachmentKey
        ? { href: loaded.href, widthPx: loaded.widthPx, heightPx: loaded.heightPx, underlay }
        : undefined,
    [wanted, underlay, loaded, attachmentKey],
  );
  return useMemo(() => ({ underlay, set, entry }), [underlay, set, entry]);
}
