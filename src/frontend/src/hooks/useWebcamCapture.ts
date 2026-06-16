import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

/**
 * REQ-029-A §0.1.1 point 4 — webcam capture via getUserMedia.
 *
 * Manages the MediaStream lifecycle: starts the rear-facing camera (falling
 * back to any camera), exposes a `videoRef` for live preview, captures a still
 * frame to a JPEG `File`, and — critically — stops every track on stop/unmount
 * so the camera indicator turns off and the device is released.
 */

export type WebcamError = 'permission_denied' | 'not_found' | 'unsupported' | 'unknown';

export interface WebcamCapture {
  isActive: boolean;
  isStarting: boolean;
  error: WebcamError | null;
  /** True when the browser exposes getUserMedia at all. */
  isSupported: boolean;
  start: () => Promise<void>;
  stop: () => void;
  /** Grab the current video frame as a JPEG File, or null if not ready. */
  capture: () => Promise<File | null>;
}

function classifyError(err: unknown): WebcamError {
  if (err instanceof DOMException) {
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') return 'permission_denied';
    if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') return 'not_found';
  }
  return 'unknown';
}

/**
 * @param videoRef ref to the live-preview `<video>` element, owned by the
 *   consuming component (keeps refs out of the hook's render-time return value).
 */
export function useWebcamCapture(
  videoRef: React.RefObject<HTMLVideoElement | null>,
): WebcamCapture {
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<WebcamError | null>(null);

  const isSupported =
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === 'function';

  const stop = useCallback(() => {
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  }, [videoRef]);

  const start = useCallback(async () => {
    if (!isSupported) {
      setError('unsupported');
      return;
    }
    setIsStarting(true);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      });
      streamRef.current = stream;
      // The <video> renders only while isActive is true, so its ref is null
      // here on first start. Flip isActive and let the effect below bind the
      // stream once the element is mounted — binding inline would race and
      // leave a black preview.
      setIsActive(true);
    } catch (err) {
      stop();
      setError(classifyError(err));
    } finally {
      setIsStarting(false);
    }
  }, [isSupported, stop]);

  const capture = useCallback(async (): Promise<File | null> => {
    const video = videoRef.current;
    if (!video || !streamRef.current) return null;
    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return null;

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.9),
    );
    if (!blob) return null;
    return new File([blob], `webcam-${Date.now()}.jpg`, { type: 'image/jpeg' });
  }, [videoRef]);

  // Bind the live stream to the <video> once it is mounted. The element is
  // conditionally rendered on isActive, so videoRef is null during start();
  // this effect runs after the element commits to the DOM and attaches the
  // stream, then plays it.
  useEffect(() => {
    const video = videoRef.current;
    const stream = streamRef.current;
    if (isActive && video && stream && video.srcObject !== stream) {
      video.srcObject = stream;
      void video.play().catch(() => undefined);
    }
  }, [isActive, videoRef]);

  // Release the camera when the consuming component unmounts.
  useEffect(() => stop, [stop]);

  return useMemo(
    () => ({ isActive, isStarting, error, isSupported, start, stop, capture }),
    [isActive, isStarting, error, isSupported, start, stop, capture],
  );
}
