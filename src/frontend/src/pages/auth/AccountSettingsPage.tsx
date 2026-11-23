import { useEffect, useMemo, useRef, type ComponentType } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink, Navigate, useLocation, useMatch } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import NotFoundPage from '@/pages/NotFoundPage';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPreferences } from '@/store/slices/userPreferencesSlice';
import AccountSettingsGroup from './settings/AccountSettingsGroup';
import DisplaySettingsGroup from './settings/DisplaySettingsGroup';
import NotificationsSettingsGroup from './settings/NotificationsSettingsGroup';
import SecuritySettingsGroup from './settings/SecuritySettingsGroup';
import IntegrationsSettingsGroup from './settings/IntegrationsSettingsGroup';
import InstallationSettingsGroup from './settings/InstallationSettingsGroup';
import SettingsNavigation, { SettingsGroupList } from './settings/SettingsNavigation';
import { useSettingsGates } from './settings/useSettingsGates';
import {
  SETTINGS_BASE_PATH,
  isSettingsGroupKey,
  resolveVisibleSettingsGroups,
  settingsGroupHeadingId,
  settingsGroupPath,
  settingsSectionElementId,
  type SettingsGroupKey,
  type SettingsGroupProps,
  type SettingsSectionKey,
} from '@/config/settingsGroups';

/**
 * Each group is its own component and owns its own state and handlers (F-11);
 * this shell only decides which group is shown and lays out the navigation.
 */
const GROUP_COMPONENTS: Record<SettingsGroupKey, ComponentType<SettingsGroupProps>> = {
  account: AccountSettingsGroup,
  display: DisplaySettingsGroup,
  notifications: NotificationsSettingsGroup,
  security: SecuritySettingsGroup,
  integrations: IntegrationsSettingsGroup,
  installation: InstallationSettingsGroup,
};

/**
 * The settings page (F-11, #2935): six groups instead of a bar of up to 14 tabs.
 *
 * Addressing: `/settings/<group>` opens a group, `/settings/<group>#<section>`
 * scrolls to a section of it. An unknown group is a 404; a known group the user
 * does not see (mode, role) lands on the first visible group; an unknown
 * section is the top of the group. The former `/settings#<tab>` links are not
 * mapped (operator decision, UI-NFR-005 R-004 exception): `/settings` opens the
 * first visible group on a desktop and the group list on a phone.
 *
 * Desktop (`md` and up, the app drawer's breakpoint): a side navigation with
 * every group next to the active group. Phone: the group list, and a tap opens
 * the group as a detail view with a back arrow.
 */
export default function AccountSettingsPage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const dispatch = useAppDispatch();
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);
  const location = useLocation();
  const groupMatch = useMatch(`${SETTINGS_BASE_PATH}/:group`);
  const requestedGroup = groupMatch?.params.group ?? null;
  const { gates, isProfilePending } = useSettingsGates();

  const groups = useMemo(() => resolveVisibleSettingsGroups(gates), [gates]);

  // The smart-home switch is a visibility gate (HA publish, HA connection), so the
  // preferences are read here rather than in the group that edits them.
  useEffect(() => {
    dispatch(fetchPreferences());
  }, [dispatch, activeTenant?.slug]);

  const isUnknownGroup = requestedGroup !== null && !isSettingsGroupKey(requestedGroup);
  const requestedVisible = groups.find((g) => g.key === requestedGroup) ?? null;
  // Desktop always shows a group; the phone's `/settings` is the group list.
  const activeGroup = requestedVisible ?? (requestedGroup === null && !isMobile ? groups[0] : null);

  const fragment = location.hash.replace(/^#/, '');
  const activeSection: SettingsSectionKey | null =
    activeGroup?.sections.find((s) => s.key === fragment)?.key ?? null;

  // Scroll to the section the fragment names, or — after moving to another group
  // or to an unknown fragment — to the top of the group. The very first render
  // without a fragment stays where the browser put it.
  const isFirstRender = useRef(true);
  const previousGroupKey = useRef<SettingsGroupKey | null>(null);
  const activeGroupKey = activeGroup?.key ?? null;
  useEffect(() => {
    const wasFirstRender = isFirstRender.current;
    const groupChanged = previousGroupKey.current !== activeGroupKey;
    isFirstRender.current = false;
    previousGroupKey.current = activeGroupKey;
    if (!activeGroupKey) return;
    const heading = document.getElementById(settingsGroupHeadingId(activeGroupKey));
    // A group opened from the navigation moves the keyboard focus to its heading,
    // so a screen-reader user hears where they landed (UI-NFR-002).
    if (groupChanged && !wasFirstRender && heading) heading.focus({ preventScroll: true });
    if (!activeSection && wasFirstRender && !fragment) return;
    const target = activeSection ? document.getElementById(settingsSectionElementId(activeSection)) : heading;
    if (target && typeof target.scrollIntoView === 'function') target.scrollIntoView({ block: 'start' });
  }, [activeGroupKey, activeSection, fragment, location.key]);

  if (isUnknownGroup) return <NotFoundPage />;

  if (requestedGroup !== null && !requestedVisible) {
    // A platform admin's deep link must not be sent away because the profile
    // carrying `is_platform_admin` has not arrived yet.
    if (isProfilePending) return <LoadingSkeleton variant="form" />;
    const fallback = groups[0];
    return <Navigate to={fallback ? settingsGroupPath(fallback.key) : SETTINGS_BASE_PATH} replace />;
  }

  const GroupComponent = activeGroup ? GROUP_COMPONENTS[activeGroup.key] : null;

  const groupDetail = activeGroup && GroupComponent && (
    <Box sx={{ flex: 1, minWidth: 0 }} data-testid={`settings-group-panel-${activeGroup.key}`}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 3 }}>
        {isMobile && (
          <IconButton
            component={RouterLink}
            to={SETTINGS_BASE_PATH}
            aria-label={t('pages.settings.backToGroups')}
            data-testid="settings-back-button"
            sx={{ ml: -1, width: 48, height: 48 }}
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        <Box sx={{ minWidth: 0, pt: isMobile ? 1 : 0 }}>
          <Typography
            id={settingsGroupHeadingId(activeGroup.key)}
            component="h2"
            variant="h5"
            tabIndex={-1}
            data-testid="settings-group-title"
            sx={{ outline: 'none', scrollMarginTop: (th) => th.spacing(10) }}
          >
            {t(activeGroup.titleKey)}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {t(activeGroup.descriptionKey)}
          </Typography>
        </Box>
      </Box>
      <GroupComponent key={activeGroup.key} sections={activeGroup.sections} />
    </Box>
  );

  return (
    <Box data-testid="account-settings-page" sx={{ mt: 2 }}>
      <PageTitle title={t('pages.settings.title')} />

      {isMobile ? (
        (groupDetail ?? <SettingsGroupList groups={groups} />)
      ) : (
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
          <Box
            sx={{
              width: 260,
              flexShrink: 0,
              position: 'sticky',
              top: (th) => th.spacing(10),
            }}
          >
            <SettingsNavigation
              groups={groups}
              variant="sidebar"
              activeGroup={activeGroup?.key}
              activeSection={activeSection}
            />
          </Box>
          {groupDetail}
        </Box>
      )}
    </Box>
  );
}
