interface BreadcrumbConfig {
  label: string;
  parent?: string;
}

export const breadcrumbMap: Record<string, BreadcrumbConfig> = {
  '/dashboard': { label: 'nav.dashboard' },
  '/stammdaten/botanical-families': {
    label: 'nav.botanicalFamilies',
    parent: '/dashboard',
  },
  '/stammdaten/species': { label: 'nav.species', parent: '/dashboard' },
  '/stammdaten/companion-planting': {
    label: 'nav.companionPlanting',
    parent: '/dashboard',
  },
  '/stammdaten/crop-rotation': { label: 'nav.cropRotation', parent: '/dashboard' },
  '/standorte/sites': { label: 'nav.sites', parent: '/dashboard' },
  '/standorte/substrates': { label: 'nav.substrates', parent: '/dashboard' },
  '/pflanzen/plant-instances': { label: 'nav.plantInstances', parent: '/dashboard' },
  '/pflanzen/calculations': { label: 'nav.calculations', parent: '/dashboard' },
};

export function buildBreadcrumbs(
  pathname: string,
): { label: string; path?: string }[] {
  const crumbs: { label: string; path?: string }[] = [];

  // Check for detail pages (with :key)
  const basePath = pathname.replace(/\/[^/]+$/, '');
  const config = breadcrumbMap[pathname] ?? breadcrumbMap[basePath];

  if (config?.parent) {
    const parentConfig = breadcrumbMap[config.parent];
    if (parentConfig) {
      crumbs.push({ label: parentConfig.label, path: config.parent });
    }
  }

  if (config) {
    if (breadcrumbMap[basePath] && basePath !== pathname) {
      crumbs.push({ label: breadcrumbMap[basePath].label, path: basePath });
      crumbs.push({ label: 'common.edit' });
    } else {
      crumbs.push({ label: config.label });
    }
  }

  return crumbs;
}
