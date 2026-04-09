interface BreadcrumbConfig {
  label: string;
  parent?: string;
  /** Override basePath for the "list" link on detail pages (when basePath is not a real route). */
  listPath?: string;
}

export const breadcrumbMap: Record<string, BreadcrumbConfig> = {
  // Dashboard
  '/dashboard': { label: 'nav.dashboard' },

  // REQ-001 Stammdaten
  '/stammdaten/botanical-families': { label: 'nav.botanicalFamilies', parent: '/dashboard' },
  '/stammdaten/species': { label: 'nav.species', parent: '/dashboard' },
  '/stammdaten/companion-planting': { label: 'nav.companionPlanting', parent: '/dashboard' },
  '/stammdaten/crop-rotation': { label: 'nav.cropRotation', parent: '/dashboard' },
  '/stammdaten/activities': { label: 'nav.activities', parent: '/dashboard' },
  '/stammdaten/import': { label: 'nav.import', parent: '/dashboard' },

  // REQ-002 Standorte
  '/standorte/sites': { label: 'nav.sites', parent: '/dashboard' },
  '/standorte/locations': { label: 'nav.sites', parent: '/dashboard', listPath: '/standorte/sites' },
  '/standorte/substrates': { label: 'nav.substrates', parent: '/dashboard' },
  '/standorte/substrates/batches': { label: 'nav.substrates', parent: '/standorte/substrates' },
  '/standorte/slots': { label: 'nav.sites', parent: '/dashboard', listPath: '/standorte/sites' },
  '/standorte/watering-events': { label: 'nav.wateringEvents', parent: '/dashboard' },

  // REQ-014 Tanks
  '/standorte/tanks': { label: 'nav.tanks', parent: '/dashboard' },

  // REQ-003 Pflanzen
  '/pflanzen/plant-instances': { label: 'nav.plantInstances', parent: '/dashboard' },
  '/pflanzen/calculations': { label: 'nav.calculations', parent: '/dashboard' },

  // REQ-004 Düngung
  '/duengung/fertilizers': { label: 'nav.fertilizers', parent: '/dashboard' },
  '/duengung/plans': { label: 'nav.nutrientPlans', parent: '/dashboard' },
  '/duengung/calculations': { label: 'nav.nutrientCalculations', parent: '/dashboard' },
  '/duengung/feeding-events': { label: 'nav.feedingEvents', parent: '/dashboard' },

  // REQ-010 Pflanzenschutz
  '/pflanzenschutz/pests': { label: 'nav.pests', parent: '/dashboard' },
  '/pflanzenschutz/diseases': { label: 'nav.diseases', parent: '/dashboard' },
  '/pflanzenschutz/treatments': { label: 'nav.treatments', parent: '/dashboard' },

  // REQ-007 Ernte
  '/ernte/batches': { label: 'nav.harvestBatches', parent: '/dashboard' },

  // REQ-006 Aufgaben
  '/aufgaben/queue': { label: 'nav.taskQueue', parent: '/dashboard' },
  '/aufgaben/tasks': { label: 'nav.taskQueue', parent: '/dashboard', listPath: '/aufgaben/queue' },
  '/aufgaben/workflows': { label: 'nav.workflows', parent: '/aufgaben/queue' },

  // REQ-003 Phase Definitions & Sequences
  '/phasen/definitionen': { label: 'pages.phaseSequences.phaseDefinitions', parent: '/dashboard' },
  '/phasen/ablaeufe': { label: 'pages.phaseSequences.phaseSequences', parent: '/dashboard' },

  // REQ-013 Durchläufe
  '/durchlaeufe/planting-runs': { label: 'nav.plantingRuns', parent: '/dashboard' },

  // Watering Log (unified)
  '/giessprotokoll': { label: 'nav.wateringLog', parent: '/dashboard' },

  // REQ-022 Pflege
  '/pflege': { label: 'nav.pflege', parent: '/dashboard' },

  // REQ-015 Kalender
  '/kalender': { label: 'nav.calendar', parent: '/dashboard' },

  // Settings
  '/settings': { label: 'nav.settings', parent: '/dashboard' },

  // Admin
  '/admin/tenants': { label: 'pages.auth.adminTenantsTitle', parent: '/settings' },
  '/admin/users': { label: 'pages.auth.adminUsersTitle', parent: '/settings' },
};

export function buildBreadcrumbs(
  pathname: string,
): { label: string; path?: string }[] {
  const crumbs: { label: string; path?: string }[] = [];

  // 1. Try exact match
  let config = breadcrumbMap[pathname];

  // 2. Try base path (strip last segment = detail page key)
  const basePath = pathname.replace(/\/[^/]+$/, '');
  if (!config) {
    config = breadcrumbMap[basePath];
  }

  // 3. Try one more level up for deeply nested paths
  //    e.g. /stammdaten/species/:speciesKey/cultivars/:cultivarKey
  const deepBase = basePath.replace(/\/[^/]+$/, '');
  if (!config && deepBase !== basePath) {
    config = breadcrumbMap[deepBase];
  }

  if (!config) return crumbs;

  // Build parent chain
  const chain: { label: string; path?: string }[] = [];

  // Walk up the parent chain (max 5 levels to prevent infinite loops)
  const parents: { label: string; path: string }[] = [];
  let parentPath = config.parent;
  for (let i = 0; i < 5 && parentPath; i++) {
    const parentConfig = breadcrumbMap[parentPath];
    if (!parentConfig) break;
    parents.unshift({ label: parentConfig.label, path: parentPath });
    parentPath = parentConfig.parent;
  }

  chain.push(...parents);

  // Is this a detail page (pathname differs from matched config path)?
  const isDetailPage = !breadcrumbMap[pathname] && breadcrumbMap[basePath];

  if (isDetailPage) {
    // List page as clickable link (listPath overrides basePath for virtual routes)
    chain.push({ label: config.label, path: config.listPath ?? basePath });
    // Detail page as current (no link)
    chain.push({ label: 'nav.detail' });
  } else {
    chain.push({ label: config.label });
  }

  return chain;
}
