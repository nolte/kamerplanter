import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import PestImageGallery from '@/components/pests/PestImageGallery';
import { createTestStore, renderWithProviders } from '../../helpers';
import type { PestImage } from '@/api/types';

vi.mock('@/api/endpoints/ipm', () => ({
  listPestImages: vi.fn(),
  deletePestImage: vi.fn(),
}));
import { listPestImages, deletePestImage } from '@/api/endpoints/ipm';

vi.mock('@/api/endpoints/adminPestRecognition', () => ({
  setPestContributionActive: vi.fn(),
  setPestImageActive: vi.fn(),
}));
import { setPestContributionActive, setPestImageActive } from '@/api/endpoints/adminPestRecognition';

/**
 * A store whose auth slice marks the user as a platform admin. Only
 * `auth.user.is_platform_admin` is read by `usePlatformAdmin`; the rest of the
 * slice is filled from the reducer's initial state.
 */
function adminStore() {
  return createTestStore({
    auth: {
      user: { is_platform_admin: true },
      isAuthenticated: true,
      isLoading: false,
    },
  });
}

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

  it('renders a recognition reference image as a native <img> with attribution and no delete', async () => {
    // Recognition tiles are GLOBAL, external, read-only — a native <img> (not
    // AuthImage), with a CC-BY attribution/license caption and no delete chrome.
    vi.mocked(listPestImages).mockResolvedValue([
      img({
        id: 'recognition:7',
        source: 'recognition',
        status: null,
        is_own: false,
        contributed_by: null,
        uri: 'https://example.org/ref/7.jpg',
        thumbnail_uri: null,
        attribution: 'Jane Doe / iNaturalist',
        license: 'CC-BY 4.0',
      }),
    ]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    const recognitionImg = screen.getByTestId('pest-image-recognition');
    // The external CC-licensed URL is used directly; privacy referrer policy set.
    expect(recognitionImg).toHaveAttribute('src', 'https://example.org/ref/7.jpg');
    expect(recognitionImg).toHaveAttribute('referrerpolicy', 'no-referrer');
    expect(recognitionImg).toHaveAttribute('loading', 'lazy');
    // CC-BY obligation: attribution + license shown next to the image.
    const attribution = screen.getByTestId('pest-image-attribution');
    expect(attribution).toHaveTextContent('Jane Doe / iNaturalist');
    expect(attribution).toHaveTextContent('CC-BY 4.0');
    // Read-only: no delete button, no global badge.
    expect(screen.queryByTestId('pest-image-delete')).toBeNull();
    expect(screen.queryByTestId('pest-image-global')).toBeNull();
  });

  it('hides a recognition tile whose external image fails to load', async () => {
    vi.mocked(listPestImages).mockResolvedValue([
      img({
        id: 'recognition:9',
        source: 'recognition',
        status: null,
        is_own: false,
        contributed_by: null,
        uri: 'https://example.org/dead-link.jpg',
        thumbnail_uri: null,
        attribution: 'Someone',
        license: 'CC0',
      }),
    ]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    await screen.findByTestId('pest-detail-gallery');
    const recognitionImg = screen.getByTestId('pest-image-recognition');
    // Simulate a dead/hotlink-blocked external image.
    fireEvent.error(recognitionImg);
    // The broken tile is removed entirely (no broken image shown).
    await waitFor(() => expect(screen.queryByTestId('pest-image-recognition')).toBeNull());
  });

  it('mixes recognition tiles with contribution and inspection tiles', async () => {
    vi.mocked(listPestImages).mockResolvedValue([
      img({ id: 'c1', source: 'contribution', is_own: true }),
      img({ id: 'a-insp', status: null, source: 'inspection', is_own: true, contributed_by: null }),
      img({
        id: 'recognition:7',
        source: 'recognition',
        status: null,
        is_own: false,
        contributed_by: null,
        uri: 'https://example.org/ref/7.jpg',
        thumbnail_uri: null,
        attribution: 'Jane Doe',
        license: 'CC0',
      }),
    ]);
    renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

    const gallery = await screen.findByTestId('pest-detail-gallery');
    // AuthImage-backed tiles: contribution + inspection (recognition uses native <img>).
    expect(within(gallery).getAllByTestId('pest-detail-image')).toHaveLength(2);
    expect(screen.getByTestId('pest-image-recognition')).toBeInTheDocument();
    expect(screen.getByTestId('pest-image-inspection')).toBeInTheDocument();
    // Only the own contribution is deletable.
    expect(screen.getAllByTestId('pest-image-delete')).toHaveLength(1);
  });

  describe('platform-admin curation', () => {
    beforeEach(() => {
      vi.mocked(setPestContributionActive).mockResolvedValue({
        id: 'c1',
        pest_key: 'p1',
        status: 'private',
        is_active: false,
        promoted_at: null,
        promoted_by: null,
      });
      vi.mocked(setPestImageActive).mockResolvedValue({ label: 'spider_mites', id: 7, is_active: false });
    });

    it('does NOT show curation controls for a non-admin user', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'c1', source: 'contribution', is_own: false, status: 'promoted' }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />);

      await screen.findByTestId('pest-detail-gallery');
      expect(screen.queryByTestId('pest-gallery-show-deselected')).toBeNull();
      expect(screen.queryByTestId('pest-image-deselect')).toBeNull();
    });

    it('shows the "show deselected" toggle and a deselect button for an admin', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'c1', source: 'contribution', is_own: false, status: 'promoted' }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />, { store: adminStore() });

      await screen.findByTestId('pest-detail-gallery');
      expect(screen.getByTestId('pest-gallery-show-deselected')).toBeInTheDocument();
      expect(screen.getByTestId('pest-image-deselect')).toBeInTheDocument();
    });

    it('reloads with include_inactive when the admin enables the toggle', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'c1', source: 'contribution', is_own: false, status: 'promoted' }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />, { store: adminStore() });

      await screen.findByTestId('pest-detail-gallery');
      // Default load: active-only, plain single-arg call.
      expect(listPestImages).toHaveBeenCalledWith('p1');

      await userEvent.click(screen.getByTestId('pest-gallery-show-deselected'));
      await waitFor(() =>
        expect(listPestImages).toHaveBeenCalledWith('p1', { includeInactive: true }),
      );
    });

    it('deselects a contribution via the admin contributions endpoint', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'c1', source: 'contribution', is_own: false, status: 'promoted' }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />, { store: adminStore() });

      await screen.findByTestId('pest-detail-gallery');
      await userEvent.click(screen.getByTestId('pest-image-deselect'));

      await waitFor(() => expect(setPestContributionActive).toHaveBeenCalledWith('p1', 'c1', false));
      // The recognition endpoint must NOT be used for a contribution tile.
      expect(setPestImageActive).not.toHaveBeenCalled();
    });

    it('deselects a recognition tile via the inference-service endpoint', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({
          id: 'recognition:7',
          source: 'recognition',
          status: null,
          is_own: false,
          contributed_by: null,
          uri: 'https://example.org/ref/7.jpg',
          thumbnail_uri: null,
          attribution: 'Jane Doe',
          license: 'CC0',
        }),
      ]);
      renderWithProviders(
        <PestImageGallery pestKey="p1" pestName="Spinnmilbe" detectionSlug="spider_mites" />,
        { store: adminStore() },
      );

      await screen.findByTestId('pest-detail-gallery');
      await userEvent.click(screen.getByTestId('pest-image-deselect'));

      await waitFor(() =>
        expect(setPestImageActive).toHaveBeenCalledWith('spider_mites', 7, {
          is_active: false,
          reason: expect.any(String),
        }),
      );
      // The contributions endpoint must NOT be used for a recognition tile.
      expect(setPestContributionActive).not.toHaveBeenCalled();
    });

    it('does not offer a deselect control for inspection photos', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'a-insp', status: null, source: 'inspection', is_own: true, contributed_by: null }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />, { store: adminStore() });

      await screen.findByTestId('pest-detail-gallery');
      expect(screen.getByTestId('pest-image-inspection')).toBeInTheDocument();
      // Inspection tiles are not curatable — no deselect, no delete.
      expect(screen.queryByTestId('pest-image-deselect')).toBeNull();
      expect(screen.queryByTestId('pest-image-delete')).toBeNull();
    });

    it('dims a deselected tile and shows a badge in the admin inactive view', async () => {
      vi.mocked(listPestImages).mockResolvedValue([
        img({ id: 'c1', source: 'contribution', is_own: false, status: 'promoted', is_active: false }),
      ]);
      renderWithProviders(<PestImageGallery pestKey="p1" pestName="Spinnmilbe" />, { store: adminStore() });

      await screen.findByTestId('pest-detail-gallery');
      expect(screen.getByTestId('pest-image-deselected-badge')).toBeInTheDocument();
      // A deselected tile offers a re-include action (its own deselect button label flips).
      expect(screen.getByTestId('pest-image-deselect')).toBeInTheDocument();
    });
  });
});
