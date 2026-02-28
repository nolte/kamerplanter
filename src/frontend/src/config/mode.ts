export const KAMERPLANTER_MODE =
  (import.meta.env.VITE_KAMERPLANTER_MODE as string) || 'full';

export const isLightMode = KAMERPLANTER_MODE === 'light';
export const isFullMode = KAMERPLANTER_MODE === 'full';
