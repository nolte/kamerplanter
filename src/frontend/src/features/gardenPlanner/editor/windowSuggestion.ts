/**
 * Which windows of the plan count for a location, and what they suggest (REQ-053 GP-FR-181, WP 10.7).
 *
 * A window counts when its line comes within the site's radius (`window_thresholds.suggestion_radius_m`, 1.5 m by
 * default) of the location's shape, edge to edge (`edgeDistanceM`, the GP-FR-167 primitive). Its facing comes from
 * the plan's north angle and outline (`windowFacing`); the suggestion from `suggestSunWindow`. No distance
 * weighting. Pure: no I/O, no React - the preview the dialog shows before anything is written.
 */
import type { PlanModel } from '../model/planModel';
import { edgeDistanceM } from '../model/geometryDistance';
import {
  contribution,
  isTropical,
  suggestSunWindow,
  windowFacing,
  type SuggestedSunWindow,
  type SunWindowSuggestion,
  type WindowFacing,
} from '../model/windowOrientation';
import type { GardenObject } from '../model/types';

export interface NearbyWindow {
  key: string;
  label: string;
  facing: WindowFacing;
  /** Edge-to-edge distance to the location, metres (rounded to 0.001). */
  distanceM: number;
  /** What this window contributes; `null` = diffuse light only, or nothing between the tropics. */
  contribution: SuggestedSunWindow | null;
}

export interface WindowSuggestionPreview {
  /** The location has a shape on the plan; without one no distance can be measured. */
  placed: boolean;
  windows: NearbyWindow[];
  suggestion: SunWindowSuggestion;
}

/** The facing of a window object on this plan, `null` when it has no wall direction. */
export function facingOf(plan: PlanModel, window: GardenObject): WindowFacing | null {
  return windowFacing(window.geometry, plan.settings?.north_angle_deg ?? 0, plan.settings?.boundary ?? null);
}

/** Whether the plan holds at least one window object. */
export function planHasWindows(plan: PlanModel): boolean {
  return Object.values(plan.gardenObjects).some((object) => object.object_type === 'window');
}

export function previewWindowSuggestion(
  plan: PlanModel,
  locationKey: string,
  radiusM: number,
  latitude: number | null,
): WindowSuggestionPreview {
  const geometry = plan.locations[locationKey]?.geometry ?? null;
  if (geometry === null) {
    return { placed: false, windows: [], suggestion: suggestSunWindow([], latitude) };
  }
  const tropical = isTropical(latitude);
  const windows: NearbyWindow[] = [];
  for (const object of Object.values(plan.gardenObjects)) {
    if (object.object_type !== 'window') continue;
    const facing = facingOf(plan, object);
    if (facing === null) continue;
    const distanceM = edgeDistanceM(object.geometry, geometry);
    if (distanceM > radiusM) continue;
    windows.push({
      key: object.key,
      label: object.label,
      facing,
      distanceM,
      contribution: tropical ? null : contribution(facing.azimuthDeg, latitude),
    });
  }
  windows.sort((a, b) => a.distanceM - b.distanceM || a.key.localeCompare(b.key));
  return {
    placed: true,
    windows,
    suggestion: suggestSunWindow(
      windows.map((window) => window.facing.azimuthDeg),
      latitude,
    ),
  };
}
