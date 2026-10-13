import client from '@/api/client';
import type { CredentialStepUp, TenantImport, TenantImportMemberGrant } from '@/api/types';

/**
 * Importing a tenant archive as a **new** tenant (REQ-056 §8.4, #2138) — platform admin only,
 * full mode only, never with an API key. Not to be confused with `import.ts`, the CSV import of
 * master data.
 */
const BASE = '/admin/platform/tenant-imports';

/**
 * How long the upload may take before the browser gives up. The server verifies the whole archive
 * before it answers (checksums, ownership of every row, catalogue entries, quotas), so a large
 * archive needs minutes, not the seconds a JSON request needs.
 */
export const TENANT_IMPORT_UPLOAD_TIMEOUT_MS = 15 * 60 * 1000;

export interface TenantImportRequestInput {
  /** The archive as exported (`kamerplanter-tenant-export/1`, a ZIP file). */
  archive: File;
  /** Archive user key → the account and role the admin confirms; empty = no member is carried over. */
  memberMapping: Readonly<Record<string, TenantImportMemberGrant>>;
  /** Plan of the new tenant; omitted = the installation's default plan. */
  planKey?: string;
  /** The admin's own step-up for `tenant_import`, bound to `archive:<first 32 hex of the SHA-256>`. */
  stepUp: CredentialStepUp;
  /** Upload progress in percent (0–100), when the browser can tell the total. */
  onUploadProgress?: (percent: number) => void;
}

/**
 * Upload an archive and request its import — `202 Accepted` with the pending record.
 *
 * The server checks the step-up first, then verifies the archive completely before anything is
 * written: `422` with an `IMPORT_*` code (`details` lists the offending entries), `422
 * MEMBER_LIMIT_REACHED`, `409 STORAGE_QUOTA_EXCEEDED` / `PHOTO_QUOTA_EXCEEDED` for the target plan,
 * `413` above the upload ceiling and `429` past `RATE_LIMIT_TENANT_IMPORT`. Only supplied fields
 * are sent.
 */
export async function requestTenantImport({
  archive,
  memberMapping,
  planKey,
  stepUp,
  onUploadProgress,
}: TenantImportRequestInput): Promise<TenantImport> {
  const form = new FormData();
  form.append('archive', archive, archive.name);
  if (Object.keys(memberMapping).length > 0) {
    form.append('member_mapping', JSON.stringify(memberMapping));
  }
  if (planKey) form.append('plan_key', planKey);
  if (stepUp.current_password !== undefined)
    form.append('current_password', stepUp.current_password);
  if (stepUp.step_up_code !== undefined) form.append('step_up_code', stepUp.step_up_code);
  if (stepUp.step_up_token !== undefined) form.append('step_up_token', stepUp.step_up_token);

  const { data } = await client.post<TenantImport>(BASE, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: TENANT_IMPORT_UPLOAD_TIMEOUT_MS,
    onUploadProgress: onUploadProgress
      ? (event) => {
          if (event.total)
            onUploadProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)));
        }
      : undefined,
  });
  return data;
}

/** The import's state and, once it ran, its report (counts per collection) — `404` for an unknown key. */
export async function getTenantImport(importKey: string): Promise<TenantImport> {
  const { data } = await client.get<TenantImport>(`${BASE}/${encodeURIComponent(importKey)}`);
  return data;
}
