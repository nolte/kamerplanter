import axios from 'axios';
import { isApiError, parseApiError } from '@/api/errors';
import type { TenantImportStatus } from '@/api/types';
import { formatNumber } from '@/utils/formatting';

/**
 * The backend's **default** for `TENANT_IMPORT_MAX_UPLOAD_MB` (`settings.tenant_import_max_upload_mb`).
 *
 * A hint, never a limit: the operator may set another value, and the general upload ceiling
 * (`STORAGE_MAX_FILE_SIZE_MB` + 1 MiB, default 26 MiB) and the ingress apply in front of the route
 * and are usually lower. The server's answer decides; the page only warns before a likely refusal.
 */
export const TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB = 512;

/** Prefix of the step-up target of `tenant_import` (`IMPORT_TARGET_PREFIX` in the backend). */
export const TENANT_IMPORT_STEP_UP_TARGET_PREFIX = 'archive:';

/** Hex digits of the archive's SHA-256 the step-up target carries (`_IMPORT_TARGET_DIGITS`). */
const TARGET_DIGITS = 32;

/** Most members `member_mapping` may list (the backend refuses more with 422). */
export const TENANT_IMPORT_MAX_MAPPED_MEMBERS = 1000;

/** States in which the import is still on its way — the page polls while one of them holds. */
const ACTIVE_STATUSES: ReadonlySet<TenantImportStatus> = new Set([
  'pending',
  'validating',
  'running',
]);

export function isActiveImport(status: TenantImportStatus): boolean {
  return ACTIVE_STATUSES.has(status);
}

/**
 * The step-up target the backend binds `tenant_import` to: `archive:` and the first 32 hex digits
 * of the upload's SHA-256. A code or a fresh-sign-in token is only accepted for exactly this file.
 *
 * `undefined` where the browser offers no Web Crypto (an insecure context, i.e. plain HTTP on a
 * host other than localhost): the password still confirms, only the code and the fresh sign-in
 * cannot be bound — the backend then refuses them, it does not accept them unbound.
 */
export async function archiveStepUpTarget(file: Blob): Promise<string | undefined> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) return undefined;
  const digest = await subtle.digest('SHA-256', await file.arrayBuffer());
  const hex = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join(
    '',
  );
  return `${TENANT_IMPORT_STEP_UP_TARGET_PREFIX}${hex.slice(0, TARGET_DIGITS)}`;
}

/** Size in MB (or kB below one MB), locale-formatted. */
export function formatArchiveSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${formatNumber(Math.max(1, Math.round(bytes / 1024)))} kB`;
  }
  return `${formatNumber(bytes / (1024 * 1024), { maximumFractionDigits: 1 })} MB`;
}

/** Whether a file is larger than the default ceiling — a reason to warn, never to block. */
export function exceedsDefaultCeiling(bytes: number): boolean {
  return bytes > TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB * 1024 * 1024;
}

/** Whether the name looks like the ZIP archive an export produces. */
export function looksLikeZip(file: File): boolean {
  return file.name.toLowerCase().endsWith('.zip') || file.type === 'application/zip';
}

/**
 * Refusal codes the page has its own explanation for (`pages.tenantImports.refusal.<code>`); any
 * other code reads as `UNKNOWN`, with the backend's message beside it.
 */
export const KNOWN_REFUSAL_CODES = [
  'IMPORT_FORMAT_UNSUPPORTED',
  'IMPORT_CHECKSUM_MISMATCH',
  'IMPORT_UNDECLARED_REFERENCE',
  'IMPORT_MISSING_CATALOG_ENTRIES',
  'IMPORT_MEMBER_NOT_FOUND',
  'MEMBER_LIMIT_REACHED',
  'STORAGE_QUOTA_EXCEEDED',
  'PHOTO_QUOTA_EXCEEDED',
  'PAYLOAD_TOO_LARGE',
  'REQUEST_BODY_TOO_LARGE',
  'UPLOAD_CAPACITY_EXHAUSTED',
  'RATE_LIMIT_EXCEEDED',
  'VALIDATION_ERROR',
  'NETWORK',
] as const;

export type ImportRefusalCode = (typeof KNOWN_REFUSAL_CODES)[number] | 'UNKNOWN';

/**
 * Failure codes a finished run can carry (`failure_reason`) that have their own explanation
 * (`pages.tenantImports.failure.<code>`); others fall back to `UNKNOWN` with the raw code shown.
 */
export const KNOWN_FAILURE_CODES = [
  'IMPORT_FORMAT_UNSUPPORTED',
  'IMPORT_CHECKSUM_MISMATCH',
  'IMPORT_UNDECLARED_REFERENCE',
  'IMPORT_MISSING_CATALOG_ENTRIES',
  'IMPORT_MEMBER_NOT_FOUND',
  'MEMBER_LIMIT_REACHED',
  'STORAGE_QUOTA_EXCEEDED',
  'PHOTO_QUOTA_EXCEEDED',
  'IMPORT_STORAGE',
  'IMPORT_ABANDONED',
  'IMPORT_FAILED',
] as const;

export function failureCodeKey(code: string | null): string {
  return code && (KNOWN_FAILURE_CODES as readonly string[]).includes(code) ? code : 'UNKNOWN';
}

/** Why the server did not take the archive — shown on the page, not inside the step-up dialog. */
export interface ImportRefusal {
  code: ImportRefusalCode;
  /** The code as the server sent it (for `UNKNOWN` shown verbatim, so it can be looked up). */
  rawCode: string;
  /** The offending entries from `details` (catalogue entries, archive user keys, parts). */
  entries: string[];
  /** The ceiling in MB the server named in a `413`, when it named one. */
  limitMb: number | null;
  /** The backend's own (English) message — shown only for an unknown code. */
  message: string;
}

/** Codes under which `details[].reason` lists entries rather than repeating the message. */
const LISTING_CODES: ReadonlySet<string> = new Set([
  'IMPORT_FORMAT_UNSUPPORTED',
  'IMPORT_CHECKSUM_MISMATCH',
  'IMPORT_UNDECLARED_REFERENCE',
  'IMPORT_MISSING_CATALOG_ENTRIES',
  'IMPORT_MEMBER_NOT_FOUND',
]);

/**
 * Whether the error refuses the **step-up itself** (wrong or missing factor, lockout, a fresh sign-in
 * needed) — the dialog shows those and stays open. Everything else is about the archive or the
 * request and closes the dialog: the step-up was accepted, the import was not.
 */
export function isStepUpRefusal(error: unknown): boolean {
  if (!isApiError(error)) return false;
  if (error.errorCode.startsWith('STEP_UP_')) return true;
  if (error.details.some((d) => d.code?.startsWith('STEP_UP_'))) return true;
  if (error.statusCode === 401) return true;
  return error.statusCode === 429 && error.errorCode !== 'RATE_LIMIT_EXCEEDED';
}

function limitFromMessage(message: string): number | null {
  const match = /(\d+)\s*MB/.exec(message);
  return match ? Number(match[1]) : null;
}

/** The refusal of an import request, read from whatever the server (or a proxy in front) answered. */
export function describeImportRefusal(error: unknown): ImportRefusal {
  if (isApiError(error)) {
    const known = (KNOWN_REFUSAL_CODES as readonly string[]).includes(error.errorCode);
    const code = (known ? error.errorCode : 'UNKNOWN') as ImportRefusalCode;
    const entries = LISTING_CODES.has(error.errorCode)
      ? error.details.map((d) => d.reason).filter((reason) => reason && reason !== error.message)
      : [];
    const tooLarge = error.statusCode === 413;
    return {
      code: tooLarge && !known ? 'PAYLOAD_TOO_LARGE' : code,
      rawCode: error.errorCode,
      entries,
      limitMb: tooLarge ? limitFromMessage(error.message) : null,
      message: error.message,
    };
  }
  if (axios.isAxiosError(error)) {
    // A proxy or ingress answers without the API's envelope: only the status is reliable.
    const status = error.response?.status;
    if (status === 413) {
      return {
        code: 'PAYLOAD_TOO_LARGE',
        rawCode: '413',
        entries: [],
        limitMb: null,
        message: error.message,
      };
    }
    if (status === undefined) {
      return {
        code: 'NETWORK',
        rawCode: error.code ?? 'NETWORK',
        entries: [],
        limitMb: null,
        message: error.message,
      };
    }
    return {
      code: 'UNKNOWN',
      rawCode: String(status),
      entries: [],
      limitMb: null,
      message: error.message,
    };
  }
  return {
    code: 'UNKNOWN',
    rawCode: 'UNKNOWN',
    entries: [],
    limitMb: null,
    message: parseApiError(error),
  };
}
