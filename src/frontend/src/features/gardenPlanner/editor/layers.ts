/**
 * The layer registry of the plan (REQ-053 GP-FR-031): one entry per switchable layer. The grid has had its
 * own switch since the MVP; further layers (the irrigation zones, "last watered", the underlay and the sun /
 * moisture / frost layers today; later the plant state) are added HERE and appear in the view bar, in the stored
 * per-user choice and in the legend without another edit of the bar. The underlay (GP-FR-033) is shown or hidden
 * per user; the editor lists its switch only while the site has a picture.
 */
export const LAYERS = [
  { id: 'grid', defaultVisible: true, bar: 'grid' },
  { id: 'zones', defaultVisible: false, bar: 'toggle' },
  { id: 'lastWatered', defaultVisible: false, bar: 'toggle' },
  { id: 'underlay', defaultVisible: true, bar: 'toggle' },
  // The site-condition layers (GP-FR-169): read from the plan's own site conditions (#2538), off until switched on.
  { id: 'sun', defaultVisible: false, bar: 'toggle' },
  { id: 'moisture', defaultVisible: false, bar: 'toggle' },
  { id: 'frost', defaultVisible: false, bar: 'toggle' },
] as const;

export type LayerId = (typeof LAYERS)[number]['id'];
export type LayerPrefs = Record<LayerId, boolean>;

/** Layers that get a toggle of their own in the layer group of the view bar (the grid has its own control). */
export const TOGGLE_LAYERS: readonly LayerId[] = LAYERS.filter((layer) => layer.bar === 'toggle').map(
  (layer) => layer.id,
);

export const DEFAULT_LAYER_PREFS: LayerPrefs = Object.fromEntries(
  LAYERS.map((layer) => [layer.id, layer.defaultVisible]),
) as LayerPrefs;
