import type { GardenObjectType } from '../model/types';

/** 24 x 24 glyphs drawn at the object centre from `ICON_MIN_PX` on (GP-NFR-067). Deliberately plain. */
const TREE = 'M12 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM11 14h2v8h-2z';
const BUILDING = 'M3 11l9-8 9 8v10H3zM10 14h4v7h-4z';
const LINE = 'M3 12h18';
const DROP = 'M12 2C8 8 6 11 6 14a6 6 0 0 0 12 0c0-3-2-6-6-12z';
const BOX = 'M4 4h16v16H4zM8 8h8v8H8z';
const DOT = 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10z';
const BAR = 'M3 10h18v4H3z';
const WINDOW = 'M5 4h14v16H5zM5 12h14M12 4v16';
const DOOR = 'M6 3h12v18H6zM15 12h1';
const LAMP = 'M12 3a5 5 0 0 0-3 9v3h6v-3a5 5 0 0 0-3-9zM9 18h6v3H9z';
const BUSH = 'M5 18a4 4 0 0 1 1-7 5 5 0 0 1 9-2 4 4 0 0 1 4 9z';

export const OBJECT_ICON_PATHS: Record<GardenObjectType, string> = {
  tree: TREE,
  shrub: BUSH,
  building: BUILDING,
  wall: BAR,
  fence: BAR,
  trellis: WINDOW,
  path: LINE,
  lawn: BUSH,
  water_source: DROP,
  compost: BOX,
  storage: BOX,
  other: DOT,
  window: WINDOW,
  door: DOOR,
  furniture: BOX,
  lamp: LAMP,
};
