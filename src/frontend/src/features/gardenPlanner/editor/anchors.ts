/** DOM ids the skip links and the focus returns aim at (REQ-053 GP-NFR-070). */
export const EDITOR_ANCHORS = {
  list: 'garden-plan-object-list',
  canvas: 'garden-plan-canvas',
  /** The side panel (§17.3, WP 10.5; the properties panel before); the third skip link aims at it. */
  panel: 'garden-plan-properties-panel',
} as const;
