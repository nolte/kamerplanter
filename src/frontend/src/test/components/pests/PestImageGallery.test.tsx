import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import PestImageGallery from '@/components/pests/PestImageGallery';
import { renderWithProviders } from '../../helpers';
import type { PestImage } from '@/api/types';

vi.mock('@/api/endpoints/ipm', () => ({
  listPestImages: vi.fn(),
  deletePestImage: vi.fn(),
}));
import { listPestImages, deletePestImage } from '@/api/endpoints/ipm';

// AuthImage does an authenticated fetch — stub it to a plain img for the test.
vi.mock('@/components/common/AuthImage', () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} data-testid="pest-detail-image" />,
}));

// The contribute dialog wraps the camera panel (getUserMedia) — stub it.
vi.mock('@/components/pests/PestImageContributeDialog', () => ({
  default: ({ open }: { open: boolean }) =>
    open ? <div data-testid="pest-contribute-dialog-stub" /> : null,
}));

function img(overrides: Partial<PestImage> = {}): PestImage {
  return {
    id: 'i1',
    pest_key: 'p1',
    attachment_id: 'a1',
    uri: '/api/v1/t/t1/attachments/a1',
    thumbnail_uri: '/api/v1/t/t1/attachments/a1/thumbnails/512',
    status: 'private',
    caption: null,
    contributed_by: 'u1',
    created_at: null,
    is_own: true,
    ...overrides,
  };
}

describe('PestImageGallery', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('loads and renders the contributed images', async () => {
    vi.mocked(listPestImages).mockResolvedValue([img({ id: 'i1' }), img({ id: 'i2' })]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    const gallery = await screen.findByTestId('pest-detail-gallery');
    expect(within(gallery).getAllByTestId('pest-detail-image')).toHaveLength(2);
    expect(listPestImages).toHaveBeenCalledWith('p1');
  });

  it('shows an empty-state hint and a contribute button when there are no images', async () => {
    vi.mocked(listPestImages).mockResolvedValue([]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    expect(await screen.findByTestId('pest-detail-no-images')).toBeInTheDocument();
    expect(screen.getByTestId('pest-contribute-button')).toBeInTheDocument();
  });

  it('opens the contribute dialog when the button is clicked', async () => {
    vi.mocked(listPestImages).mockResolvedValue([]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-contribute-button');
    await userEvent.click(screen.getByTestId('pest-contribute-button'));
    expect(screen.getByTestId('pest-contribute-dialog-stub')).toBeInTheDocument();
  });

  it('opens a confirmation dialog when the delete button is clicked', async () => {
    vi.mocked(listPestImages).mockResolvedValue([img({ id: 'i1', is_own: true })]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    // Clicking pest-image-delete must open the ConfirmDialog — not delete immediately.
    await userEvent.click(screen.getByTestId('pest-image-delete'));
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    expect(deletePestImage).not.toHaveBeenCalled();
  });

  it('deletes an own image after confirmation', async () => {
    vi.mocked(listPestImages).mockResolvedValue([img({ id: 'i1', is_own: true })]);
    vi.mocked(deletePestImage).mockResolvedValue();
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    // Step 1: click delete to open confirmation.
    await userEvent.click(screen.getByTestId('pest-image-delete'));
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();

    // Step 2: confirm deletion.
    await userEvent.click(screen.getByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(deletePestImage).toHaveBeenCalledWith('p1', 'i1'));
    await waitFor(() => expect(screen.queryByTestId('pest-detail-image')).toBeNull());
  });

  it('cancels deletion and keeps the image when cancel is clicked', async () => {
    vi.mocked(listPestImages).mockResolvedValue([img({ id: 'i1', is_own: true })]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    await userEvent.click(screen.getByTestId('pest-image-delete'));
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('confirm-dialog-cancel'));
    expect(deletePestImage).not.toHaveBeenCalled();
    expect(screen.getByTestId('pest-detail-image')).toBeInTheDocument();
  });

  it('marks a globally promoted image and hides delete for non-owned images', async () => {
    vi.mocked(listPestImages).mockResolvedValue([img({ id: 'i1', status: 'promoted', is_own: false })]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    expect(screen.getByTestId('pest-image-global')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-image-delete')).toBeNull();
  });

  it('renders inspection-sourced photos read-only with a provenance badge', async () => {
    // Inspection photos report is_own=true but must NOT be deletable; they carry
    // their own provenance badge instead of the global / delete chrome.
    vi.mocked(listPestImages).mockResolvedValue([
      img({ id: 'a-insp', status: null, source: 'inspection', is_own: true, contributed_by: null }),
    ]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    expect(screen.getByTestId('pest-image-inspection')).toBeInTheDocument();
    // Read-only: neither a delete button nor the global badge.
    expect(screen.queryByTestId('pest-image-delete')).toBeNull();
    expect(screen.queryByTestId('pest-image-global')).toBeNull();
  });

  it('shows both contribution and inspection tiles together', async () => {
    vi.mocked(listPestImages).mockResolvedValue([
      img({ id: 'c1', source: 'contribution', is_own: true }),
      img({ id: 'a-insp', status: null, source: 'inspection', is_own: true, contributed_by: null }),
    ]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    const gallery = await screen.findByTestId('pest-detail-gallery');
    expect(within(gallery).getAllByTestId('pest-detail-image')).toHaveLength(2);
    // Contribution tile keeps its delete button; inspection tile does not.
    expect(screen.getAllByTestId('pest-image-delete')).toHaveLength(1);
    expect(screen.getByTestId('pest-image-inspection')).toBeInTheDocument();
  });

});
