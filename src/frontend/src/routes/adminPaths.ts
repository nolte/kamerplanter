/**
 * The platform administrator's hub (F-12, R-17, #2935).
 *
 * One constant rather than a literal per caller: the sidebar entry, the
 * breadcrumb parents and the back links of every admin page all lead here, and
 * the previous target (`/settings#platform`) was spelled out at eight call sites.
 * Kept out of `AdminPlatformPage` so that importing it does not pull the lazily
 * loaded page into another chunk.
 */
export const ADMIN_PLATFORM_PATH = '/admin/platform';
