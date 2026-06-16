import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { createRef } from 'react';
import { useWebcamCapture } from '@/hooks/useWebcamCapture';

/**
 * REQ-029-A §0.1.1 point 4 — webcam capture hook unit tests.
 *
 * getUserMedia, the canvas and the <video> element are all stubbed (jsdom has no
 * camera and no canvas backend). The tests cover the MediaStream lifecycle
 * (start → bind → stop), the error classifier (permission/not-found/unsupported/
 * unknown) and every early-return guard in capture().
 */

function makeVideoRef(overrides: Partial<HTMLVideoElement> = {}) {
  const video = {
    videoWidth: 640,
    videoHeight: 480,
    srcObject: null,
    play: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  } as unknown as HTMLVideoElement;
  const ref = createRef<HTMLVideoElement>();
  (ref as { current: HTMLVideoElement | null }).current = video;
  return ref;
}

function stubMediaDevices(getUserMedia: ReturnType<typeof vi.fn>) {
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia },
  });
}

function trackStream(stop = vi.fn()) {
  return { getTracks: () => [{ stop }] } as unknown as MediaStream;
}

// ── Canvas stub ──────────────────────────────────────────────────────────────
let canvasConfig: { context: object | null; blob: Blob | null };
let drawImageSpy: ReturnType<typeof vi.fn>;
let toBlobArgs: { type: string; quality: number } | null;
let createElementSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  drawImageSpy = vi.fn();
  toBlobArgs = null;
  canvasConfig = { context: { drawImage: drawImageSpy }, blob: new Blob(['x'], { type: 'image/jpeg' }) };

  createElementSpy = vi
    .spyOn(document, 'createElement')
    .mockImplementation(((tag: string) => {
      if (tag === 'canvas') {
        return {
          width: 0,
          height: 0,
          getContext: vi.fn(() => canvasConfig.context),
          toBlob: vi.fn(
            (cb: (b: Blob | null) => void, type: string, quality: number) => {
              toBlobArgs = { type, quality };
              cb(canvasConfig.blob);
            },
          ),
        } as unknown as HTMLCanvasElement;
      }
      return Object.getPrototypeOf(document).createElement.call(document, tag);
    }) as typeof document.createElement);
});

afterEach(() => {
  createElementSpy.mockRestore();
  Reflect.deleteProperty(navigator, 'mediaDevices');
  vi.restoreAllMocks();
});

describe('useWebcamCapture — support detection', () => {
  it('reports unsupported when mediaDevices is absent', () => {
    Reflect.deleteProperty(navigator, 'mediaDevices');
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    expect(result.current.isSupported).toBe(false);
  });

  it('reports supported when getUserMedia exists', () => {
    stubMediaDevices(vi.fn());
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    expect(result.current.isSupported).toBe(true);
  });

  it('start() sets the unsupported error without calling getUserMedia', async () => {
    Reflect.deleteProperty(navigator, 'mediaDevices');
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('unsupported');
    expect(result.current.isActive).toBe(false);
  });
});

describe('useWebcamCapture — start lifecycle', () => {
  it('starts the rear camera and becomes active', async () => {
    const getUserMedia = vi.fn().mockResolvedValue(trackStream());
    stubMediaDevices(getUserMedia);
    const videoRef = makeVideoRef();
    const { result } = renderHook(() => useWebcamCapture(videoRef));

    await act(async () => {
      await result.current.start();
    });

    expect(getUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({ audio: false, video: { facingMode: { ideal: 'environment' } } }),
    );
    expect(result.current.isActive).toBe(true);
    expect(result.current.error).toBeNull();
    // The effect binds the stream to the video element and plays it.
    await waitFor(() => expect(videoRef.current!.play).toHaveBeenCalled());
  });

  it('classifies a denied permission as permission_denied and stays inactive', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new DOMException('no', 'NotAllowedError'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('permission_denied');
    expect(result.current.isActive).toBe(false);
  });

  it('classifies a SecurityError as permission_denied', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new DOMException('insecure', 'SecurityError'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('permission_denied');
  });

  it('classifies a missing device as not_found', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new DOMException('gone', 'NotFoundError'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('not_found');
  });

  it('classifies an OverconstrainedError as not_found', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new DOMException('constraint', 'OverconstrainedError'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('not_found');
  });

  it('classifies any other DOMException as unknown', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new DOMException('weird', 'AbortError'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('unknown');
  });

  it('classifies a non-DOMException throw as unknown', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(new Error('boom'));
    stubMediaDevices(getUserMedia);
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.error).toBe('unknown');
  });
});

describe('useWebcamCapture — stop', () => {
  it('stops all tracks, clears srcObject and deactivates', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue(trackStream(stop));
    stubMediaDevices(getUserMedia);
    const videoRef = makeVideoRef();
    const { result } = renderHook(() => useWebcamCapture(videoRef));

    await act(async () => {
      await result.current.start();
    });
    act(() => result.current.stop());

    expect(stop).toHaveBeenCalled();
    expect(videoRef.current!.srcObject).toBeNull();
    expect(result.current.isActive).toBe(false);
  });

  it('is a no-op when no stream is active', () => {
    stubMediaDevices(vi.fn());
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    expect(() => act(() => result.current.stop())).not.toThrow();
    expect(result.current.isActive).toBe(false);
  });
});

describe('useWebcamCapture — capture()', () => {
  async function startedHook(videoRef = makeVideoRef()) {
    const getUserMedia = vi.fn().mockResolvedValue(trackStream());
    stubMediaDevices(getUserMedia);
    const hook = renderHook(() => useWebcamCapture(videoRef));
    await act(async () => {
      await hook.result.current.start();
    });
    return hook;
  }

  it('returns a JPEG File from the current frame', async () => {
    const { result } = await startedHook();
    let file: File | null = null;
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeInstanceOf(File);
    expect(file!.type).toBe('image/jpeg');
    expect(file!.name).toMatch(/^webcam-\d+\.jpg$/);
    expect(drawImageSpy).toHaveBeenCalled();
    expect(toBlobArgs).toEqual({ type: 'image/jpeg', quality: 0.9 });
  });

  it('returns null when no stream is active (capture before start)', async () => {
    stubMediaDevices(vi.fn());
    const { result } = renderHook(() => useWebcamCapture(makeVideoRef()));
    let file: File | null = new File([], 'x');
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeNull();
  });

  it('returns null when the video element is missing', async () => {
    const ref = createRef<HTMLVideoElement>();
    const { result } = await startedHook(ref);
    let file: File | null = new File([], 'x');
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeNull();
  });

  it('returns null when the video has no intrinsic dimensions yet', async () => {
    const { result } = await startedHook(makeVideoRef({ videoWidth: 0, videoHeight: 0 }));
    let file: File | null = new File([], 'x');
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeNull();
  });

  it('returns null when no 2D context is available', async () => {
    canvasConfig.context = null;
    const { result } = await startedHook();
    let file: File | null = new File([], 'x');
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeNull();
  });

  it('returns null when toBlob yields no blob', async () => {
    canvasConfig.blob = null;
    const { result } = await startedHook();
    let file: File | null = new File([], 'x');
    await act(async () => {
      file = await result.current.capture();
    });
    expect(file).toBeNull();
  });
});

describe('useWebcamCapture — unmount', () => {
  it('releases the camera on unmount', async () => {
    const stop = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue(trackStream(stop));
    stubMediaDevices(getUserMedia);
    const { result, unmount } = renderHook(() => useWebcamCapture(makeVideoRef()));
    await act(async () => {
      await result.current.start();
    });
    unmount();
    expect(stop).toHaveBeenCalled();
  });
});
