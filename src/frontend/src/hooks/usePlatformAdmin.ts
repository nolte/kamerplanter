import { useAppSelector } from '@/store/hooks';

/**
 * True when the logged-in user is a platform admin (admin membership in the
 * "platform" tenant). Sourced from the `/users/me` profile (`is_platform_admin`)
 * held in the auth slice. Gates admin-only UI such as reference-image curation.
 */
export function usePlatformAdmin(): boolean {
  return useAppSelector((s) => s.auth.user?.is_platform_admin ?? false);
}
