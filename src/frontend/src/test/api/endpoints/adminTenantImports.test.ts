import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  client: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import {
  TENANT_IMPORT_UPLOAD_TIMEOUT_MS,
  getTenantImport,
  requestTenantImport,
} from '@/api/endpoints/adminTenantImports';

const client = mocks.client;
const ARCHIVE = new File(['zip-bytes'], 'garden.zip', { type: 'application/zip' });
// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['import', 'admin', 'pw'].join('-');

function sentForm(): FormData {
  return client.post.mock.calls[0][1] as FormData;
}

beforeEach(() => {
  vi.clearAllMocks();
  client.post.mockResolvedValue({ data: { key: 'imp-1' } });
});

describe('adminTenantImports endpoints (REQ-056 §8.4, #2138)', () => {
  it('uploads the archive, the mapping as JSON, the plan and the step-up as multipart fields', async () => {
    const mapping = {
      'old-user': {
        email: 'anna@example.org',
        role: 'lead' as const,
        admin_scopes: ['management' as const],
      },
    };
    const result = await requestTenantImport({
      archive: ARCHIVE,
      memberMapping: mapping,
      planKey: 'community',
      stepUp: { current_password: PASSWORD },
    });

    expect(result).toEqual({ key: 'imp-1' });
    const [path, form, config] = client.post.mock.calls[0];
    expect(path).toBe('/admin/platform/tenant-imports');
    expect(config).toMatchObject({
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: TENANT_IMPORT_UPLOAD_TIMEOUT_MS,
    });
    expect((form as FormData).get('archive')).toBeInstanceOf(File);
    expect(((form as FormData).get('archive') as File).name).toBe('garden.zip');
    expect(JSON.parse((form as FormData).get('member_mapping') as string)).toEqual(mapping);
    expect((form as FormData).get('plan_key')).toBe('community');
    expect((form as FormData).get('current_password')).toBe(PASSWORD);
    expect((form as FormData).has('step_up_code')).toBe(false);
    expect((form as FormData).has('step_up_token')).toBe(false);
  });

  it('sends only what was supplied: no mapping, no plan, a code or a token instead of a password', async () => {
    await requestTenantImport({
      archive: ARCHIVE,
      memberMapping: {},
      stepUp: { step_up_code: '123456' },
    });
    let form = sentForm();
    expect(form.has('member_mapping')).toBe(false);
    expect(form.has('plan_key')).toBe(false);
    expect(form.has('current_password')).toBe(false);
    expect(form.get('step_up_code')).toBe('123456');

    client.post.mockClear();
    await requestTenantImport({
      archive: ARCHIVE,
      memberMapping: {},
      stepUp: { step_up_token: 'tok' },
    });
    form = sentForm();
    expect(form.get('step_up_token')).toBe('tok');
  });

  it('reports the upload progress in percent, and nothing when the total is unknown', async () => {
    const progress = vi.fn();
    await requestTenantImport({
      archive: ARCHIVE,
      memberMapping: {},
      stepUp: {},
      onUploadProgress: progress,
    });
    const onUploadProgress = client.post.mock.calls[0][2].onUploadProgress as (e: {
      loaded: number;
      total?: number;
    }) => void;
    onUploadProgress({ loaded: 25, total: 100 });
    onUploadProgress({ loaded: 50 });
    onUploadProgress({ loaded: 120, total: 100 });
    expect(progress.mock.calls).toEqual([[25], [100]]);
  });

  it('wires no progress handler when none is asked for', async () => {
    await requestTenantImport({ archive: ARCHIVE, memberMapping: {}, stepUp: {} });
    expect(client.post.mock.calls[0][2].onUploadProgress).toBeUndefined();
  });

  it('reads one import by its encoded key', async () => {
    client.get.mockResolvedValue({ data: { key: 'a b' } });
    await expect(getTenantImport('a b')).resolves.toEqual({ key: 'a b' });
    expect(client.get).toHaveBeenCalledWith('/admin/platform/tenant-imports/a%20b');
  });
});
