import { Navigate, Outlet } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { isLightMode } from '@/config/mode';

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAppSelector((s) => s.auth);

  // Light mode: no authentication required
  if (isLightMode) {
    return <Outlet />;
  }

  if (isLoading) {
    return <LoadingSkeleton variant="card" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
