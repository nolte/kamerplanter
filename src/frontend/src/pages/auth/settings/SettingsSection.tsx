import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { settingsSectionElementId, type SettingsSectionDef } from '@/config/settingsGroups';

interface SettingsSectionProps {
  section: SettingsSectionDef;
  children: ReactNode;
}

/**
 * One former tab, rendered as a section of its group (F-11). The heading names
 * it, the element id is what `/settings/<group>#<section>` scrolls to; the
 * content below is the tab's form, unchanged.
 */
export default function SettingsSection({ section, children }: SettingsSectionProps) {
  const { t } = useTranslation();
  const id = settingsSectionElementId(section.key);
  const headingId = `${id}-title`;

  return (
    <Box
      component="section"
      id={id}
      aria-labelledby={headingId}
      data-testid={`settings-section-${section.key}`}
      // Breathing room below the app bar when scrolled to; the bar's own height is the root's
      // `scroll-padding-top` (MainLayout), so the two add up to the former 80 px clearance.
      sx={{ scrollMarginTop: (theme) => theme.spacing(2) }}
    >
      <Typography
        id={headingId}
        component="h3"
        variant="subtitle1"
        sx={{ fontWeight: 600, mb: 1.5, pb: 0.5, borderBottom: 1, borderColor: 'divider' }}
      >
        {t(section.labelKey)}
      </Typography>
      {children}
    </Box>
  );
}
