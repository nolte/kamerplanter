import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import PersonOutlineIcon from '@mui/icons-material/PersonOutlined';
import TuneIcon from '@mui/icons-material/Tune';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
import DnsOutlinedIcon from '@mui/icons-material/DnsOutlined';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import {
  settingsGroupPath,
  settingsNavGroupElementId,
  type SettingsGroupKey,
  type SettingsSectionKey,
  type VisibleSettingsGroup,
} from '@/config/settingsGroups';

const GROUP_ICONS: Record<SettingsGroupKey, React.ReactNode> = {
  account: <PersonOutlineIcon />,
  display: <TuneIcon />,
  notifications: <NotificationsNoneIcon />,
  security: <LockOutlinedIcon />,
  integrations: <HubOutlinedIcon />,
  installation: <DnsOutlinedIcon />,
};

interface SettingsNavigationProps {
  groups: readonly VisibleSettingsGroup[];
  /**
   * `sidebar` — the desktop side navigation: every group, the active one
   * expanded to its sections. `list` — the phone's entry screen: every group
   * with its description, a tap opens the group's detail view.
   */
  variant: 'sidebar' | 'list';
  activeGroup?: SettingsGroupKey;
  activeSection?: SettingsSectionKey | null;
}

/**
 * The settings page's group navigation (F-11). Every entry is a real link
 * (`/settings/<group>`, `/settings/<group>#<section>`), so it can be opened in
 * a new tab and is announced as a link. The operator group is set apart below
 * a divider and its own heading.
 */
export default function SettingsNavigation({ groups, variant, activeGroup, activeSection }: SettingsNavigationProps) {
  const { t } = useTranslation();
  const isList = variant === 'list';

  return (
    <Box component="nav" aria-label={t('pages.settings.navLabel')} data-testid={`settings-nav-${variant}`}>
      <List disablePadding>
        {groups.map((group, index) => {
          const isActive = group.key === activeGroup;
          const startsOperatorBlock = group.isOperatorGroup && !groups[index - 1]?.isOperatorGroup;
          return (
            <Fragment key={group.key}>
              {startsOperatorBlock && (
                <>
                  <Divider component="li" role="presentation" sx={{ my: 1 }} />
                  <ListSubheader
                    disableSticky
                    sx={{ bgcolor: 'transparent', lineHeight: 2.5, px: isList ? 2 : 1.5 }}
                    data-testid="settings-nav-operator-heading"
                  >
                    {t('pages.settings.operatorHeading')}
                  </ListSubheader>
                </>
              )}
              <ListItem disablePadding sx={{ display: 'block', my: isList ? 0 : 0.25 }}>
                <ListItemButton
                  component={RouterLink}
                  to={settingsGroupPath(group.key)}
                  selected={isActive}
                  aria-current={isActive && !activeSection ? 'page' : undefined}
                  // The list variant's id is the focus target after the phone's back arrow.
                  id={isList ? settingsNavGroupElementId(group.key) : undefined}
                  data-testid={`settings-group-${group.key}`}
                  // UI-NFR-001 R-011 — 48px touch targets; the list rows are taller still.
                  sx={{ borderRadius: isList ? 0 : 1, minHeight: isList ? 64 : 48 }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>{GROUP_ICONS[group.key]}</ListItemIcon>
                  <ListItemText
                    primary={t(group.titleKey)}
                    secondary={isList ? t(group.descriptionKey) : undefined}
                    slotProps={{ primary: { sx: { fontWeight: isActive ? 600 : undefined } } }}
                  />
                  {isList && <ChevronRightIcon color="action" aria-hidden="true" />}
                </ListItemButton>
                {/* The active group's sections, so a long group can be entered at the section wanted. */}
                {!isList && isActive && group.sections.length > 1 && (
                  <List disablePadding dense data-testid={`settings-nav-sections-${group.key}`}>
                    {group.sections.map((section) => {
                      const isSectionActive = section.key === activeSection;
                      return (
                        <ListItem key={section.key} disablePadding>
                          <ListItemButton
                            component={RouterLink}
                            to={`${settingsGroupPath(group.key)}#${section.key}`}
                            selected={isSectionActive}
                            aria-current={isSectionActive ? 'location' : undefined}
                            data-testid={`settings-nav-section-${section.key}`}
                            sx={{ borderRadius: 1, minHeight: 48, pl: 7 }}
                          >
                            <ListItemText
                              primary={t(section.labelKey)}
                              slotProps={{ primary: { sx: { fontSize: '0.875rem' } } }}
                            />
                          </ListItemButton>
                        </ListItem>
                      );
                    })}
                  </List>
                )}
              </ListItem>
              {isList && index < groups.length - 1 && !groups[index + 1]?.isOperatorGroup && (
                <Divider component="li" role="presentation" />
              )}
            </Fragment>
          );
        })}
      </List>
    </Box>
  );
}

/** The phone's entry screen: the group list on a surface of its own. */
export function SettingsGroupList({ groups }: { groups: readonly VisibleSettingsGroup[] }) {
  return (
    <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
      <SettingsNavigation groups={groups} variant="list" />
    </Paper>
  );
}
