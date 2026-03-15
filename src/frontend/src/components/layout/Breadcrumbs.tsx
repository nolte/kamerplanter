import { useLocation, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import MuiBreadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import { useAppSelector } from '@/store/hooks';
import { buildBreadcrumbs } from '@/routes/breadcrumbs';

export default function Breadcrumbs() {
  const { t } = useTranslation();
  const location = useLocation();
  const dynamicCrumbs = useAppSelector((s) => s.ui.breadcrumbs);

  // Prefer page-supplied dynamic breadcrumbs over static path-based ones
  const crumbs = dynamicCrumbs.length > 0 ? dynamicCrumbs : buildBreadcrumbs(location.pathname);

  if (crumbs.length === 0) return null;

  return (
    <MuiBreadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        if (isLast || !crumb.path) {
          return (
            <Typography key={index} color="text.primary">
              {crumb.label.startsWith('nav.') || crumb.label.startsWith('entities.') ? t(crumb.label) : crumb.label}
            </Typography>
          );
        }
        return (
          <Link
            key={index}
            component={RouterLink}
            to={crumb.path}
            underline="hover"
            color="inherit"
          >
            {crumb.label.startsWith('nav.') || crumb.label.startsWith('entities.') ? t(crumb.label) : crumb.label}
          </Link>
        );
      })}
    </MuiBreadcrumbs>
  );
}
