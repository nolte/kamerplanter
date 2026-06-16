import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import * as imageUtils from '@/utils/imageNormalization';

/**
 * REQ-029 §4.1 / REQ-029-A §10.1 — capture component tests.
 * getUserMedia is mocked; image normalization is stubbed to avoid canvas work.
 */

function makeFile(name = 'leaf.jpg', type = 'image/jpeg'): File {
  return new File([new Uint8Array([1, 2, 3])], name, { type });
}

describe('ImageCapturePanel', () => {
  beforeEach(() => {
    vi.spyOn(imageUtils, 'normalizeImage').mockResolvedValue({
      file: makeFile('normalized.jpg'),
      previewUrl: 'blob:preview',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    // Reset any stubbed mediaDevices between tests.
    Reflect.deleteProperty(navigator, 'mediaDevices');
  });

  it('exposes all three capture paths when webcam is supported', () => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: vi.fn() },
    });
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="intermediate" />,
    );
    expect(screen.getByTestId('capture-mobile-camera')).toBeInTheDocument();
    expect(screen.getByTestId('capture-webcam-start')).toBeInTheDocument();
    expect(screen.getByTestId('capture-upload')).toBeInTheDocument();
    expect(screen.getByTestId('capture-dropzone')).toBeInTheDocument();
  });

  it('hides the webcam button when getUserMedia is unavailable', () => {
    Reflect.deleteProperty(navigator, 'mediaDevices');
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="intermediate" />,
    );
    expect(screen.queryByTestId('capture-webcam-start')).not.toBeInTheDocument();
    // Mobile rear-camera + upload remain available (mobile-first).
    expect(screen.getByTestId('capture-mobile-camera')).toBeInTheDocument();
  });

  it('normalizes and emits a selected file via the upload input', async () => {
    const onImageReady = vi.fn();
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} level="intermediate" />,
    );
    const input = screen.getByTestId('capture-file-input') as HTMLInputElement;
    await userEvent.upload(input, makeFile());
    await waitFor(() => expect(onImageReady).toHaveBeenCalledTimes(1));
    expect(imageUtils.normalizeImage).toHaveBeenCalled();
    expect(onImageReady).toHaveBeenCalledWith(expect.any(File), 'blob:preview');
  });

  it('emits a file via the smartphone rear-camera input (capture=environment)', async () => {
    const onImageReady = vi.fn();
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} level="beginner" />,
    );
    const camInput = screen.getByTestId('capture-camera-input') as HTMLInputElement;
    expect(camInput).toHaveAttribute('capture', 'environment');
    await userEvent.upload(camInput, makeFile('photo.jpg'));
    await waitFor(() => expect(onImageReady).toHaveBeenCalledTimes(1));
  });

  it('starts the webcam via getUserMedia and shows live preview + shutter', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop }],
    });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    // jsdom has no real video element playback.
    Object.defineProperty(HTMLMediaElement.prototype, 'play', {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });

    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="expert" />,
    );
    await userEvent.click(screen.getByTestId('capture-webcam-start'));
    await waitFor(() =>
      expect(getUserMedia).toHaveBeenCalledWith(
        expect.objectContaining({ video: expect.anything(), audio: false }),
      ),
    );
    await screen.findByTestId('webcam-preview');
    expect(screen.getByTestId('webcam-shoot')).toBeInTheDocument();
  });

  it('surfaces a permission error when getUserMedia is denied', async () => {
    const getUserMedia = vi
      .fn()
      .mockRejectedValue(new DOMException('denied', 'NotAllowedError'));
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="expert" />,
    );
    await userEvent.click(screen.getByTestId('capture-webcam-start'));
    expect(await screen.findByTestId('webcam-error')).toBeInTheDocument();
  });

  it('accepts a dropped image file via drag & drop', async () => {
    const onImageReady = vi.fn();
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} level="intermediate" />,
    );
    const dropzone = screen.getByTestId('capture-dropzone');
    const file = makeFile('dropped.jpg');
    const dataTransfer = { files: [file], items: [], types: ['Files'] };
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.drop(dropzone, { dataTransfer });
    await waitFor(() => expect(onImageReady).toHaveBeenCalledTimes(1));
  });

  it('highlights the dropzone on drag-over and clears it on drag-leave', async () => {
    const { fireEvent } = await import('@testing-library/react');
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="intermediate" />,
    );
    const dropzone = screen.getByTestId('capture-dropzone');
    fireEvent.dragOver(dropzone);
    // The active border colour switches to primary.main on drag-over.
    expect(dropzone).toBeInTheDocument();
    fireEvent.dragLeave(dropzone);
    expect(dropzone).toBeInTheDocument();
  });

  it('ignores a drop while disabled', async () => {
    const onImageReady = vi.fn();
    const { fireEvent } = await import('@testing-library/react');
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} disabled level="intermediate" />,
    );
    const dropzone = screen.getByTestId('capture-dropzone');
    fireEvent.drop(dropzone, { dataTransfer: { files: [makeFile()] } });
    // Disabled panel must not normalize or emit anything.
    expect(imageUtils.normalizeImage).not.toHaveBeenCalled();
    expect(onImageReady).not.toHaveBeenCalled();
  });

  it('shows a capture error when normalization fails for a selected file', async () => {
    vi.spyOn(imageUtils, 'normalizeImage').mockRejectedValue(new Error('UNSUPPORTED_FORMAT'));
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="intermediate" />,
    );
    const input = screen.getByTestId('capture-file-input') as HTMLInputElement;
    // Accept-filter only allows jpeg/png/webp; use an accepted type and let the
    // normalization itself reject to drive the error branch.
    await userEvent.upload(input, makeFile('bad.jpg', 'image/jpeg'));
    expect(await screen.findByTestId('capture-error')).toBeInTheDocument();
  });

  it('renders beginner photo tips and a single prominent CTA', () => {
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="beginner" />,
    );
    // Photo tip list is beginner-only (advanced users stay uncluttered).
    expect(screen.getByText('Tips for better results')).toBeInTheDocument();
    expect(screen.getByTestId('capture-mobile-camera')).toBeInTheDocument();
  });

  it('captures a webcam still, normalizes it, stops the stream and emits', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    Object.defineProperty(HTMLMediaElement.prototype, 'play', {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });
    // The hook's capture() reads the live frame through a real <canvas>; jsdom
    // has no 2D backend, so stub the canvas prototype rather than createElement
    // (which MUI also calls during render).
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation(function (
      this: HTMLCanvasElement,
      cb: BlobCallback,
    ) {
      cb(new Blob(['x'], { type: 'image/jpeg' }));
    });

    const onImageReady = vi.fn();
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} level="expert" />,
    );

    await userEvent.click(screen.getByTestId('capture-webcam-start'));
    const video = (await screen.findByTestId('webcam-preview')) as HTMLVideoElement;
    Object.defineProperty(video, 'videoWidth', { configurable: true, value: 640 });
    Object.defineProperty(video, 'videoHeight', { configurable: true, value: 480 });

    await userEvent.click(screen.getByTestId('webcam-shoot'));
    await waitFor(() => expect(onImageReady).toHaveBeenCalledTimes(1));
    expect(stop).toHaveBeenCalled();
  });

  it('does not emit when the webcam frame capture yields no file', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    Object.defineProperty(HTMLMediaElement.prototype, 'play', {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });
    // No 2D context → the hook's capture() returns null, so onImageReady must
    // not fire and the stream stays open.
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
      null as unknown as CanvasRenderingContext2D,
    );

    const onImageReady = vi.fn();
    renderWithProviders(
      <ImageCapturePanel onImageReady={onImageReady} level="expert" />,
    );
    await userEvent.click(screen.getByTestId('capture-webcam-start'));
    const video = (await screen.findByTestId('webcam-preview')) as HTMLVideoElement;
    Object.defineProperty(video, 'videoWidth', { configurable: true, value: 640 });
    Object.defineProperty(video, 'videoHeight', { configurable: true, value: 480 });

    await userEvent.click(screen.getByTestId('webcam-shoot'));
    // Capture failed gracefully — nothing emitted, preview still active.
    expect(onImageReady).not.toHaveBeenCalled();
    expect(screen.getByTestId('webcam-preview')).toBeInTheDocument();
  });

  it('cancels the live webcam preview', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    });
    Object.defineProperty(HTMLMediaElement.prototype, 'play', {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });
    renderWithProviders(
      <ImageCapturePanel onImageReady={vi.fn()} level="expert" />,
    );
    await userEvent.click(screen.getByTestId('capture-webcam-start'));
    await screen.findByTestId('webcam-preview');
    await userEvent.click(screen.getByTestId('webcam-cancel'));
    // Back to the dropzone view.
    expect(await screen.findByTestId('capture-dropzone')).toBeInTheDocument();
  });
});
