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
});
