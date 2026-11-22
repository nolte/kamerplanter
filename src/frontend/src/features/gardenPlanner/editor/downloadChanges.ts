import type { PlanOperation } from '../model/types';

/** File format of "keep my changes as a copy" (GP-UX-017). Personal data is never part of it. */
export interface PlanChangesFile {
  format: 'kamerplanter.garden-plan-changes';
  version: 1;
  site_key: string;
  /** The revision the changes were made on. */
  based_on_revision: number;
  /** The revision on the server when the save was refused. */
  current_revision: number | null;
  operations: PlanOperation[];
}

export function buildChangesFile(
  siteKey: string,
  basedOnRevision: number,
  currentRevision: number | null,
  operations: readonly PlanOperation[],
): PlanChangesFile {
  return {
    format: 'kamerplanter.garden-plan-changes',
    version: 1,
    site_key: siteKey,
    based_on_revision: basedOnRevision,
    current_revision: currentRevision,
    operations: [...operations],
  };
}

export function changesFileName(siteKey: string, basedOnRevision: number): string {
  return `garden-plan-changes-${siteKey}-rev${basedOnRevision}.json`;
}

/** Hand the file to the browser as a download. */
export function downloadChangesFile(file: PlanChangesFile): void {
  const blob = new Blob([JSON.stringify(file, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = changesFileName(file.site_key, file.based_on_revision);
  anchor.click();
  URL.revokeObjectURL(url);
}
