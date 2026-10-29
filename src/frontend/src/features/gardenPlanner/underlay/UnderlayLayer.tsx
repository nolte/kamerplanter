import type { UnderlayRenderEntry } from '../renderer/types';
import { underlayTransform } from './calibration';

/**
 * The background picture of the plan (REQ-053 GP-FR-033), drawn **first** in the plan SVG so every bed, object and
 * plant stands above it, and in the editor only (the SVG/PDF export and the JSON export never carry it by default).
 * Decorative: `aria-hidden`, no pointer events - tracing over it must not steal a click from the object below the
 * cursor, and what the picture shows is not information the plan states.
 */
export function UnderlayLayer({ layer }: { layer: UnderlayRenderEntry }) {
  const transform = underlayTransform(layer.underlay);
  if (transform === null) return null;
  return (
    <g data-plan-underlay="" aria-hidden="true" pointerEvents="none" transform={transform}>
      <image
        href={layer.href}
        width={layer.widthPx}
        height={layer.heightPx}
        opacity={layer.underlay.opacity}
        preserveAspectRatio="none"
      />
    </g>
  );
}
