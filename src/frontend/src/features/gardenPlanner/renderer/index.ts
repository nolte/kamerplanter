/**
 * The renderer boundary as the editor sees it: the interface, its value types and the label hook.
 * `SvgPlanRenderer` is deliberately NOT exported here - only the route that mounts the editor
 * chooses an implementation (GP-NFR-009; ESLint forbids `editor/**` from importing it).
 */
export type {
  PlanRenderer,
  RenderOptions,
  RenderSelection,
  RendererLabels,
  Viewport,
} from './types';
export { BOUNDARY_KEY } from './planIndex';
export { useRendererLabels } from './useRendererLabels';
