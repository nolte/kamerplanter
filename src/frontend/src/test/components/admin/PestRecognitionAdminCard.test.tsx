import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import { PestRecognitionAdminCard } from '@/components/admin/PestRecognitionAdminCard';
import type { PestRecognitionStatus, PestCurationImageList } from '@/api/types';

vi.mock('@/api/endpoints/adminPestRecognition', () => ({
  getPestRecognitionStatus: vi.fn(),
  startPestAcquisition: vi.fn(),
  getPestClassImages: vi.fn(),
  setPestImageActive: vi.fn(),
}));

import * as api from '@/api/endpoints/adminPestRecognition';

const mockStatus = api.getPestRecognitionStatus as unknown as ReturnType<typeof vi.fn>;
const mockStart = api.startPestAcquisition as unknown as ReturnType<typeof vi.fn>;
const mockImages = api.getPestClassImages as unknown as ReturnType<typeof vi.fn>;
const mockSetActive = api.setPestImageActive as unknown as ReturnType<typeof vi.fn>;

function status(overrides: Partial<PestRecognitionStatus> = {}): PestRecognitionStatus {
  return {
    feature_enabled: true,
    service_ready: true,
    index_count: 12,
    target_per_class: 30,
    classes: [
      {
        label: 'spider_mite',
        common_name: 'Spinnmilbe',
        category: 'pest',
        scientific_name: 'Tetranychus urticae',
        gbif_taxon_key: '2130185',
        total: 12,
        active: 12,
        target: 30,
        usable: false,
      },
    ],
    ...overrides,
  };
}

const IMAGES: PestCurationImageList = {
  label: 'spider_mite',
  count: 1,
  active_count: 1,
  images: [
    {
      id: 1,
      source_url: 'https://example.org/mite.jpg',
      license: 'CC-BY',
      attribution: 'Jane Doe',
      source: 'gbif',
      source_record_id: 'r1',
      is_active: true,
      exclusion_reason: null,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockStart.mockResolvedValue({ status: 'queued', task_id: 't1' });
  mockImages.mockResolvedValue(IMAGES);
  mockSetActive.mockResolvedValue({ label: 'spider_mite', id: 1, is_active: false });
});

describe('PestRecognitionAdminCard', () => {
  it('shows a discreet hint when the feature is disabled', async () => {
    mockStatus.mockResolvedValue(status({ feature_enabled: false }));
    renderWithProviders(<PestRecognitionAdminCard />);
    expect(await screen.findByTestId('pest-recognition-disabled')).toBeInTheDocument();
  });

  it('renders coverage per class and the index count', async () => {
    mockStatus.mockResolvedValue(status());
    renderWithProviders(<PestRecognitionAdminCard />);
    expect(await screen.findByTestId('pest-recognition-details')).toBeInTheDocument();
    expect(screen.getByTestId('pest-recognition-chip-count')).toHaveTextContent('12');
    expect(screen.getByTestId('pest-class-count-spider_mite')).toHaveTextContent('12/30');
  });

  it('starts the acquisition job from the button', async () => {
    mockStatus.mockResolvedValue(status());
    renderWithProviders(<PestRecognitionAdminCard />);
    const btn = await screen.findByTestId('pest-recognition-acquire-button');
    await userEvent.click(btn);
    expect(mockStart).toHaveBeenCalledTimes(1);
  });

  it('loads and displays images with attribution when a class is expanded', async () => {
    mockStatus.mockResolvedValue(status());
    renderWithProviders(<PestRecognitionAdminCard />);
    const row = await screen.findByTestId('pest-class-spider_mite');
    await userEvent.click(row.querySelector('button')!);
    await waitFor(() => expect(mockImages).toHaveBeenCalledWith('spider_mite'));
    expect(await screen.findByTestId('pest-reference-image')).toBeInTheDocument();
    expect(screen.getByText('© Jane Doe · CC-BY')).toBeInTheDocument();
  });

  it('deselects a reference image with a reason so it no longer affects detection', async () => {
    mockStatus.mockResolvedValue(status());
    renderWithProviders(<PestRecognitionAdminCard />);
    const row = await screen.findByTestId('pest-class-spider_mite');
    await userEvent.click(row.querySelector('button')!);
    await screen.findByTestId('pest-reference-image');

    await userEvent.click(screen.getByTestId('pest-deselect-button'));
    expect(await screen.findByTestId('pest-deselect-dialog')).toBeInTheDocument();
    await userEvent.click(screen.getByTestId('pest-deselect-confirm'));

    await waitFor(() =>
      expect(mockSetActive).toHaveBeenCalledWith('spider_mite', 1, { is_active: false, reason: 'blurry' }),
    );
  });
});
