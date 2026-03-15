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
      setRemaining((prev) => {
        if (prev <= 1) {
          setRunning(false);
          setExpired(true);
          // Beep via Web Audio API
          try {
            const ctx = audioRef.current ?? new AudioContext();
            audioRef.current = ctx;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            gain.gain.value = 0.3;
            osc.start();
            osc.stop(ctx.currentTime + 0.3);
          } catch {
            // Audio not available — ignore
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running, expired]);

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
