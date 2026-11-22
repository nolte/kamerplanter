import { useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { isLightMode } from '@/config/mode';
import { isInvitationAcceptPath, rememberPendingInvitation } from '@/utils/pendingInvitation';
import { forgetLoginReturn, loginPathFor } from '@/utils/loginReturn';

export default function ProtectedRoute() {
  const { isAuthenticated, initialized } = useAppSelector((s) => s.auth);
  const location = useLocation();

  // UI-NFR-014 R-010: a protected page reached signed in is where the sign-in was meant to lead - or a later
  // visit; either way the remembered return path has done its job.
  useEffect(() => {
    if (!isLightMode && isAuthenticated) forgetLoginReturn();
  }, [isAuthenticated]);

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
    // UI-NFR-014 R-009 — every other page (a bed label's QR deep link, GP-UX-028, among them) is named in the
    // login URL; the login page carries it through the sign-in.
    return <Navigate to={loginPathFor(location)} replace />;
  }

  return <Outlet />;
}
