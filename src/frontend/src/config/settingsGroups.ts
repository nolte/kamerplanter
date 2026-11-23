/**
 * The settings page's structure (F-11, #2935): six groups, each holding the
 * former tabs as sections.
 *
 * This table is the one place that decides which section exists, which group
 * holds it and who sees it. The group components render a section only when it
 * is listed as visible here, the navigation lists exactly these groups, and the
 * in-app links build their targets from it ({@link settingsSectionPath}) — so a
 * section cannot be reachable from the navigation and missing from the page, or
 * linked at a place it no longer lives.
 *
 * The visibility gates are the ones the tab bar used, applied per section:
 * light vs. full mode (REQ-027), the user's smart-home switch, and
 * `canManageInstanceSettings` (operator: light mode, or a platform admin in
 * full mode). A group without a visible section is not shown.
 */

export const SETTINGS_BASE_PATH = '/settings';

export type SettingsGroupKey =
  | 'account'
  | 'display'
  | 'notifications'
  | 'security'
  | 'integrations'
  | 'installation';

export type SettingsSectionKey =
  | 'profile'
  | 'account'
  | 'experience'
  | 'kiosk'
  | 'modules'
  | 'dashboard'
  | 'notifications'
  | 'security'
  | 'sessions'
  | 'apikeys'
  | 'connect'
  | 'ha'
  | 'ha-publish'
  | 'storage'
  | 'weather-providers'
  | 'ha-connection'
  | 'plant-identification'
  | 'recognition';

/** What a section's visibility is decided on. */
export interface SettingsGates {
  /** REQ-027 light mode: no accounts, so no security, sessions or account deletion. */
  lightMode: boolean;
  /** The user's own smart-home switch (`smart_home_enabled`). */
  smartHomeEnabled: boolean;
  /** Installation-wide configuration: light mode, or a platform admin in full mode (#1385). */
  canManageInstanceSettings: boolean;
}

export interface SettingsSectionDef {
  key: SettingsSectionKey;
  /** i18n key of the section heading. */
  labelKey: string;
  isVisible: (gates: SettingsGates) => boolean;
}

export interface SettingsGroupDef {
  key: SettingsGroupKey;
  titleKey: string;
  descriptionKey: string;
  /**
   * The operator group: set apart in the navigation by a divider and a heading,
   * because what it configures applies to the whole installation, not to the
   * signed-in user.
   */
  isOperatorGroup: boolean;
  sections: readonly SettingsSectionDef[];
}

/** A group as the current user sees it: only its visible sections. */
export interface VisibleSettingsGroup extends Omit<SettingsGroupDef, 'sections'> {
  sections: readonly SettingsSectionDef[];
}

const always = (): boolean => true;
const fullModeOnly = (g: SettingsGates): boolean => !g.lightMode;
const lightModeOnly = (g: SettingsGates): boolean => g.lightMode;
const operatorOnly = (g: SettingsGates): boolean => g.canManageInstanceSettings;

export const SETTINGS_GROUPS: readonly SettingsGroupDef[] = [
  {
    key: 'account',
    titleKey: 'pages.settings.groups.account.title',
    descriptionKey: 'pages.settings.groups.account.description',
    isOperatorGroup: false,
    sections: [
      { key: 'profile', labelKey: 'pages.settings.sections.profile', isVisible: always },
      // Accounts exist in full mode only (REQ-027).
      { key: 'account', labelKey: 'pages.settings.sections.account', isVisible: fullModeOnly },
    ],
  },
  {
    key: 'display',
    titleKey: 'pages.settings.groups.display.title',
    descriptionKey: 'pages.settings.groups.display.description',
    isOperatorGroup: false,
    sections: [
      { key: 'experience', labelKey: 'pages.settings.sections.experience', isVisible: always },
      { key: 'kiosk', labelKey: 'pages.settings.sections.kiosk', isVisible: always },
      { key: 'modules', labelKey: 'pages.settings.sections.modules', isVisible: always },
      // REQ-045 sets no mode restriction; the tab bar offered it in light mode only,
      // which left the dashboard's own link into it dead in full mode (F-11).
      { key: 'dashboard', labelKey: 'pages.settings.sections.dashboard', isVisible: always },
    ],
  },
  {
    key: 'notifications',
    titleKey: 'pages.settings.groups.notifications.title',
    descriptionKey: 'pages.settings.groups.notifications.description',
    isOperatorGroup: false,
    sections: [
      { key: 'notifications', labelKey: 'pages.settings.sections.notifications', isVisible: always },
    ],
  },
  {
    key: 'security',
    titleKey: 'pages.settings.groups.security.title',
    descriptionKey: 'pages.settings.groups.security.description',
    isOperatorGroup: false,
    sections: [
      { key: 'security', labelKey: 'pages.settings.sections.security', isVisible: fullModeOnly },
      { key: 'sessions', labelKey: 'pages.settings.sections.sessions', isVisible: fullModeOnly },
      // API keys exist in both modes: they are the only credential the MCP interface accepts (REQ-033 §4.3).
      { key: 'apikeys', labelKey: 'pages.settings.sections.apikeys', isVisible: always },
      // #1118 P12 — light mode's credential-free instance-discovery QR; full mode
      // pairs a device from the sessions section instead.
      { key: 'connect', labelKey: 'pages.settings.sections.connect', isVisible: lightModeOnly },
    ],
  },
  {
    key: 'integrations',
    titleKey: 'pages.settings.groups.integrations.title',
    descriptionKey: 'pages.settings.groups.integrations.description',
    isOperatorGroup: false,
    sections: [
      // The per-user smart-home switch — the personal half of the former `ha` tab.
      { key: 'ha', labelKey: 'pages.settings.sections.ha', isVisible: always },
      { key: 'ha-publish', labelKey: 'pages.settings.sections.haPublish', isVisible: (g) => g.smartHomeEnabled },
    ],
  },
  {
    key: 'installation',
    titleKey: 'pages.settings.groups.installation.title',
    descriptionKey: 'pages.settings.groups.installation.description',
    isOperatorGroup: true,
    sections: [
      { key: 'storage', labelKey: 'pages.settings.sections.storage', isVisible: operatorOnly },
      { key: 'weather-providers', labelKey: 'pages.settings.sections.weatherProviders', isVisible: operatorOnly },
      // The instance-wide half of the former `ha` tab (one HA and one Pl@ntNet key per installation).
      // The HA connection keeps its second condition: it only matters once smart home is on.
      {
        key: 'ha-connection',
        labelKey: 'pages.settings.sections.haConnection',
        isVisible: (g) => g.canManageInstanceSettings && g.smartHomeEnabled,
      },
      {
        key: 'plant-identification',
        labelKey: 'pages.settings.sections.plantIdentification',
        isVisible: operatorOnly,
      },
      { key: 'recognition', labelKey: 'pages.settings.sections.recognition', isVisible: operatorOnly },
    ],
  },
];

const GROUP_KEYS: ReadonlySet<string> = new Set(SETTINGS_GROUPS.map((g) => g.key));

export function isSettingsGroupKey(value: string): value is SettingsGroupKey {
  return GROUP_KEYS.has(value);
}

/** The groups the user sees, each with only its visible sections; empty groups are dropped. */
export function resolveVisibleSettingsGroups(gates: SettingsGates): VisibleSettingsGroup[] {
  return SETTINGS_GROUPS.map((group) => ({
    ...group,
    sections: group.sections.filter((section) => section.isVisible(gates)),
  })).filter((group) => group.sections.length > 0);
}

/** The group that holds `section` — every section lives in exactly one. */
export function settingsGroupOf(section: SettingsSectionKey): SettingsGroupKey {
  const group = SETTINGS_GROUPS.find((g) => g.sections.some((s) => s.key === section));
  if (!group) throw new Error(`Unknown settings section: ${section}`);
  return group.key;
}

export function settingsGroupPath(group: SettingsGroupKey): string {
  return `${SETTINGS_BASE_PATH}/${group}`;
}

/** The deep link of a section, `/settings/<group>#<section>` — what every in-app link uses. */
export function settingsSectionPath(section: SettingsSectionKey): string {
  return `${settingsGroupPath(settingsGroupOf(section))}#${section}`;
}

/** The DOM id of a section's anchor; scrolled to when the URL fragment names it. */
export function settingsSectionElementId(section: string): string {
  return `settings-section-${section}`;
}

/** The DOM id of a group's heading — the "top of the group" an unknown fragment lands on. */
export function settingsGroupHeadingId(group: string): string {
  return `settings-group-heading-${group}`;
}

/** What the shell hands every group component: the group's visible sections. */
export interface SettingsGroupProps {
  sections: readonly SettingsSectionDef[];
}

/** The visible section `key` of a group, or `undefined` when the user does not see it. */
export function findSettingsSection(
  sections: readonly SettingsSectionDef[],
  key: SettingsSectionKey,
): SettingsSectionDef | undefined {
  return sections.find((section) => section.key === key);
}
