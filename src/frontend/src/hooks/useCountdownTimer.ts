import { useState, useCallback, useEffect, useRef, useMemo } from 'react';

interface CountdownState {
  remaining: number;
  running: boolean;
  expired: boolean;
  start: () => void;
  pause: () => void;
  reset: () => void;
}

export function useCountdownTimer(totalSeconds: number): CountdownState {
  const [remaining, setRemaining] = useState(totalSeconds);
  const [running, setRunning] = useState(false);
  const [expired, setExpired] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (!running || expired) return;

    intervalRef.current = setInterval(() => {
      // The updater stays pure: React may run it twice (#3022).
      setRemaining((prev) => Math.max(prev - 1, 0));
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running, expired]);

  useEffect(() => {
    if (!running || remaining > 0) return;
    setRunning(false);
    setExpired(true);
    beep(audioRef);
  }, [running, remaining]);

  // The audio context holds a system audio stream until it is closed.
  useEffect(
    () => () => {
      void audioRef.current?.close().catch((err: unknown) => {
        // Closing an already closed context rejects; the stream is released either way.
        console.debug('[countdown] closing the audio context failed', err);
      });
      audioRef.current = null;
    },
    [],
  );

  const start = useCallback(() => {
    if (expired) return;
    setRunning(true);
  }, [expired]);

  const pause = useCallback(() => {
    setRunning(false);
  }, []);

  const reset = useCallback(() => {
    setRunning(false);
    setExpired(false);
    setRemaining(totalSeconds);
  }, [totalSeconds]);

  return useMemo(
    () => ({ remaining, running, expired, start, pause, reset }),
    [remaining, running, expired, start, pause, reset],
  );
}

/** One short 880 Hz tone; the context is closed once the tone has ended. */
function beep(audioRef: { current: AudioContext | null }): void {
  try {
    const ctx = new AudioContext();
    audioRef.current = ctx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.value = 0.3;
    osc.onended = () => {
      if (audioRef.current === ctx) audioRef.current = null;
      void ctx.close().catch((err: unknown) => {
        // Same as the unmount cleanup: a failed close leaves nothing to undo.
        console.debug('[countdown] closing the audio context failed', err);
      });
    };
    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch {
    // Audio not available — ignore
  }
}
