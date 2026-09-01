import { useEffect, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { SxProps, Theme } from '@mui/material/styles';
import { useRoleRestriction } from '@/auth/roleRestriction';

interface PageTitleProps {
  title: string;
  /** Optional action element (e.g. "Create" button) rendered next to the title.
   *  Wraps below the title on small screens automatically.
   *
   *  **Suppressed on a route that `<RequireRole>` restricted** (#1261). The header
   *  action of a role-guarded route is by construction the gated write the route
   *  was guarded for — that is the criterion `ROLE_GUARDED_ROUTES` applies — so a
   *  member who may not perform it must not be offered it. Reading the restriction
   *  once, here, is what keeps the guard from being opt-in at 71 call sites; on
   *  every unguarded route the context reports `restricted: false` and this is a
   *  no-op. */
  action?: ReactNode;
  /** Optional meta-row content (Pattern C, UI-NFR-017 §3.3 R-010..R-012):
   *  status chips, badges, manufacturer text. Rendered as a second row below
   *  the title row, vertically aligned to its centre, with `flexWrap: 'wrap'`. */
  meta?: ReactNode;
  sx?: SxProps<Theme>;
}

export default function PageTitle({ title, action: requestedAction, meta, sx }: PageTitleProps) {
  const { restricted } = useRoleRestriction();
  const action = restricted ? undefined : requestedAction;

  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);

  if (!action && !meta) {
    return (
      <Typography variant="h4" component="h1" sx={{ mb: 3, ...sx as object }} data-testid="page-title">
        {title}
      </Typography>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: 1,
        mb: 3,
        ...sx as object,
      }}
    >
      {/* Left side: title (and meta-row stacked below it per Pattern C) */}
      <Box sx={{ minWidth: 0, flex: '1 1 auto' }}>
        <Typography variant="h4" component="h1" data-testid="page-title" sx={{ mb: 0 }}>
          {title}
        </Typography>
        {meta && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1,
              mt: 0.5,
            }}
            data-testid="page-title-meta"
          >
            {meta}
          </Box>
        )}
      </Box>
      {/* Right side: action zone. It MUST stay shrinkable — a flex item with
          `flexShrink: 0` is sized to its max-content width, so any
          `flexWrap: 'wrap'` inside the action group never took effect and a
          multi-button header pushed the whole document past the viewport width
          (measured 918px at a 393px viewport on the task queue). Shrinking is
          bounded by the group's automatic minimum size (min-content), so the
          buttons wrap instead of overflowing — UI-NFR-001 R-005/R-006,
          UI-NFR-021 R-023. */}
      {action && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            flexWrap: 'wrap',
            gap: 1,
          }}
          data-testid="page-title-actions"
        >
          {action}
        </Box>
      )}
    </Box>
  );
}
