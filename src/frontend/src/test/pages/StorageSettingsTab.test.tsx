import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../helpers';
import StorageSettingsTab from '@/pages/auth/StorageSettingsTab';
import type { StorageSettingsResponse } from '@/api/endpoints/adminSettings';

// Mock the admin settings API module (NFR-013 storage endpoints).
vi.mock('@/api/endpoints/adminSettings', () => ({
  getStorageSettings: vi.fn(),
  updateStorageSettings: vi.fn(),
  testStorageConnection: vi.fn(),
}));

import {
  getStorageSettings,
  updateStorageSettings,
  testStorageConnection,
} from '@/api/endpoints/adminSettings';

const mockGet = vi.mocked(getStorageSettings);
const mockUpdate = vi.mocked(updateStorageSettings);
const mockTest = vi.mocked(testStorageConnection);

function buildSettings(overrides: Partial<StorageSettingsResponse> = {}): StorageSettingsResponse {
  return {
    backend: 'local-fs',
    local_fs_root: '/data/attachments',
    local_fs_public_base_url: '',
    s3_endpoint_url: '',
    s3_region: '',
    s3_bucket: '',
    s3_use_path_style: false,
    s3_kms_key_id: '',
    s3_force_tls: true,
    s3_access_key_id_configured: false,
    s3_secret_access_key_configured: false,
    source_backend: 'env',
    source_local_fs_root: 'env',
    source_local_fs_public_base_url: 'env',
    source_s3_endpoint_url: 'env',
    source_s3_region: 'env',
    source_s3_bucket: 'env',
    source_s3_use_path_style: 'env',
    source_s3_kms_key_id: 'env',
    source_s3_force_tls: 'env',
    ...overrides,
  };
}

describe('StorageSettingsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows local-fs fields by default and no S3 fields', async () => {
    mockGet.mockResolvedValue(buildSettings());
    renderWithProviders(<StorageSettingsTab />);

    expect(await screen.findByTestId('storage-local-fs-fields')).toBeInTheDocument();
    expect(screen.queryByTestId('storage-s3-fields')).not.toBeInTheDocument();
  });

  it('switches to S3 fields when the S3 backend is selected', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildSettings());
    renderWithProviders(<StorageSettingsTab />);

    await screen.findByTestId('storage-local-fs-fields');
    await user.click(screen.getByTestId('storage-backend-s3'));

    expect(await screen.findByTestId('storage-s3-fields')).toBeInTheDocument();
    expect(screen.queryByTestId('storage-local-fs-fields')).not.toBeInTheDocument();
    // Conditional S3 fields appear.
    expect(screen.getByTestId('storage-s3-bucket')).toBeInTheDocument();
    expect(screen.getByTestId('storage-s3-region')).toBeInTheDocument();
  });

  it('never renders raw S3 credentials, only a presence hint', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(
      buildSettings({ backend: 's3', s3_access_key_id_configured: true, s3_secret_access_key_configured: true }),
    );
    renderWithProviders(<StorageSettingsTab />);

    const hint = await screen.findByTestId('storage-s3-credentials-hint');
    expect(hint).toBeInTheDocument();
    // There is no input for the access key or secret anywhere in the tab.
    expect(screen.queryByTestId('storage-s3-access-key-id')).not.toBeInTheDocument();
    expect(screen.queryByTestId('storage-s3-secret-access-key')).not.toBeInTheDocument();
    void user; // keep symmetry; not needed beyond render
  });

  it('runs the connection test and shows the result', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildSettings());
    mockTest.mockResolvedValue({
      success: true,
      backend: 'local-fs',
      message: 'Storage path is writable.',
      writable: true,
    });
    renderWithProviders(<StorageSettingsTab />);

    await screen.findByTestId('storage-test-button');
    await user.click(screen.getByTestId('storage-test-button'));

    const result = await screen.findByTestId('storage-test-result');
    expect(result).toHaveTextContent('writable');
    expect(mockTest).toHaveBeenCalledTimes(1);
  });

  it('saves the selected backend via update', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildSettings());
    mockUpdate.mockResolvedValue({
      home_assistant: {
        ha_url: '',
        ha_access_token_masked: '',
        ha_timeout: 10,
        source_ha_url: 'env',
        source_ha_access_token: 'env',
        source_ha_timeout: 'env',
      },
      plant_identification: { plantnet_api_key_masked: '', source_plantnet_api_key: 'none' },
      storage: buildSettings({ backend: 's3', source_backend: 'db' }),
    });
    renderWithProviders(<StorageSettingsTab />);

    await screen.findByTestId('storage-local-fs-fields');
    await user.click(screen.getByTestId('storage-backend-s3'));
    await user.click(screen.getByTestId('storage-save-button'));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledTimes(1);
    });
    // Saved payload selects the s3 backend and carries no credential fields.
    const payload = mockUpdate.mock.calls[0][0];
    expect(payload.backend).toBe('s3');
    expect(payload).not.toHaveProperty('s3_access_key_id');
    expect(payload).not.toHaveProperty('s3_secret_access_key');
  });
});
