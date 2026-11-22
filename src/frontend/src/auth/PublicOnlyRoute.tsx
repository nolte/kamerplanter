import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { postLoginPath } from '@/utils/pendingInvitation';

export default function PublicOnlyRoute() {
  const { isAuthenticated, initialized } = useAppSelector((s) => s.auth);
  const { search } = useLocation();

  // Only gate on the one-time auth bootstrap. Gating on `isLoading` would unmount
  // the login/register page during an in-flight submit — losing its form state and
  // the freshly-set error before it can render. The pages own their submit feedback
  // via their loading buttons.
  if (!initialized) {
    return <LoadingSkeleton variant="card" />;
  }

  if (isAuthenticated) {
    // #2162 — a pending invitation (remembered by ProtectedRoute) continues where it left off;
    // UI-NFR-014 R-010 — else the login page's `returnTo` (a session restored on `/login?returnTo=…`).
    return <Navigate to={postLoginPath(search)} replace />;
  }

  return <Outlet />;
}
