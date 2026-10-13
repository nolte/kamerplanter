import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { isLightMode } from '@/config/mode';
import { isInvitationAcceptPath, rememberPendingInvitation } from '@/utils/pendingInvitation';

export default function ProtectedRoute() {
  const { isAuthenticated, initialized } = useAppSelector((s) => s.auth);
  const location = useLocation();

  // Light mode: no authentication required
  if (isLightMode) {
    return <Outlet />;
  }

  // Wait for the one-time auth bootstrap to conclude before deciding, so a valid
  // session restored via refresh does not flash a redirect to /login. Once
  // bootstrap is done, an unauthenticated direct hit still redirects. Gating on
  // `isLoading` instead would bounce back to the skeleton on every in-flight
  // request (e.g. profile refetch), which is not the intent here.
  if (!initialized) {
    return <LoadingSkeleton variant="card" />;
  }

  if (!isAuthenticated) {
    // #2162 — an invitation link opened without a session keeps its token across the sign-in;
    // `postLoginPath()` brings the visitor back to the accept page afterwards.
    if (isInvitationAcceptPath(location.pathname)) {
      rememberPendingInvitation(new URLSearchParams(location.search).get('token') ?? '');
    }
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
