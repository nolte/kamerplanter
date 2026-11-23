import { describe, it, expect } from 'vitest';
import i18n from 'i18next';
import {
  SETTINGS_GROUPS,
  isSettingsGroupKey,
  resolveVisibleSettingsGroups,
  settingsGroupOf,
  settingsSectionPath,
  type SettingsGates,
  type SettingsSectionKey,
} from '@/config/settingsGroups';

/**
 * F-11 (#2935) — the settings page's group table.
 *
 * acceptance-2: every former tab is reachable exactly once, in the group it was
 * assigned to; the dashboard settings in both modes.
 * acceptance-3: the gates of the tab bar apply unchanged per section, the
 * Installation group is the operator's only, and an empty group is dropped.
 */

/** The tab bar before F-11, per mode, with every gate open (`AccountSettingsPage.tsx` @ a958541c6). */
const FORMER_TABS_LIGHT = [
  'profile', 'notifications', 'experience', 'kiosk', 'modules', 'dashboard', 'connect', 'apikeys', 'ha',
  'ha-publish', 'storage', 'weather-providers',
] as const;
const FORMER_TABS_FULL = [
  'profile', 'notifications', 'experience', 'kiosk', 'modules', 'security', 'sessions', 'apikeys', 'ha',
  'ha-publish', 'storage', 'weather-providers', 'account',
] as const;
/** The instance-wide cards of the former `ha` tab, now sections of Installation. */
const FORMER_HA_INSTANCE_CARDS = ['ha-connection', 'plant-identification', 'recognition'] as const;

/** Operator decision 2026-11-17 (R3, R14, R15): where each section lives. */
const EXPECTED_GROUP: Record<SettingsSectionKey, string> = {
  profile: 'account',
  account: 'account',
  experience: 'display',
  kiosk: 'display',
  modules: 'display',
  dashboard: 'display',
  notifications: 'notifications',
  security: 'security',
  sessions: 'security',
  apikeys: 'security',
  connect: 'security',
  ha: 'integrations',
  'ha-publish': 'integrations',
  storage: 'installation',
  'weather-providers': 'installation',
  'ha-connection': 'installation',
  'plant-identification': 'installation',
  recognition: 'installation',
};

const ALL_OPEN = { smartHomeEnabled: true, canManageInstanceSettings: true };

function visibleSections(gates: SettingsGates): string[] {
  return resolveVisibleSettingsGroups(gates).flatMap((g) => g.sections.map((s) => s.key));
}

describe('settings groups — inventory (acceptance-2)', () => {
  it('declares six groups, the operator group last', () => {
    expect(SETTINGS_GROUPS.map((g) => g.key)).toEqual([
      'account', 'display', 'notifications', 'security', 'integrations', 'installation',
    ]);
    expect(SETTINGS_GROUPS.filter((g) => g.isOperatorGroup).map((g) => g.key)).toEqual(['installation']);
  });

  it('places every section in exactly one group, the one the operator assigned', () => {
    const all = SETTINGS_GROUPS.flatMap((g) => g.sections.map((s) => [s.key, g.key] as const));
    expect(new Set(all.map(([s]) => s)).size).toBe(all.length);
    expect(Object.fromEntries(all)).toEqual(EXPECTED_GROUP);
  });

  it.each([
    ['light', true, FORMER_TABS_LIGHT],
    ['full', false, FORMER_TABS_FULL],
  ] as const)('keeps every former %s-mode tab reachable exactly once', (_mode, lightMode, formerTabs) => {
    const sections = visibleSections({ lightMode, ...ALL_OPEN });
    for (const tab of formerTabs) {
      expect(sections.filter((s) => s === tab), tab).toHaveLength(1);
    }
    // Nothing else besides the former tabs, the split ha cards and the dashboard fix.
    const expected = new Set<string>([...formerTabs, ...FORMER_HA_INSTANCE_CARDS, 'dashboard']);
    expect(new Set(sections)).toEqual(expected);
    expect(sections).toHaveLength(expected.size);
  });

  it('shows the dashboard settings in both modes (R14)', () => {
    expect(visibleSections({ lightMode: true, smartHomeEnabled: false, canManageInstanceSettings: false })).toContain('dashboard');
    expect(visibleSections({ lightMode: false, smartHomeEnabled: false, canManageInstanceSettings: false })).toContain('dashboard');
  });

  it('builds every deep link as /settings/<group>#<section>', () => {
    expect(settingsSectionPath('dashboard')).toBe('/settings/display#dashboard');
    expect(settingsSectionPath('ha')).toBe('/settings/integrations#ha');
    expect(settingsSectionPath('modules')).toBe('/settings/display#modules');
    expect(settingsGroupOf('weather-providers')).toBe('installation');
    expect(isSettingsGroupKey('installation')).toBe(true);
    expect(isSettingsGroupKey('platform')).toBe(false);
  });

  it.each(['de', 'en'])('labels every group and section in %s', async (lng) => {
    await i18n.changeLanguage(lng);
    for (const group of SETTINGS_GROUPS) {
      for (const key of [group.titleKey, group.descriptionKey, ...group.sections.map((s) => s.labelKey)]) {
        expect(i18n.exists(key, { lng }), `${lng}:${key}`).toBe(true);
      }
    }
    await i18n.changeLanguage('de');
  });
});

describe('settings groups — gate matrix (acceptance-3)', () => {
  const MATRIX = [true, false].flatMap((lightMode) =>
    [true, false].flatMap((smartHomeEnabled) =>
      [true, false].map((canManageInstanceSettings) => ({ lightMode, smartHomeEnabled, canManageInstanceSettings })),
    ),
  );

  it.each(MATRIX)('applies the former tab gates per section (%o)', (gates) => {
    const sections = new Set(visibleSections(gates));
    const expect_ = (key: string, visible: boolean) => expect(sections.has(key), key).toBe(visible);

    // light vs. full mode
    expect_('security', !gates.lightMode);
    expect_('sessions', !gates.lightMode);
    expect_('account', !gates.lightMode);
    expect_('connect', gates.lightMode);
    // always
    for (const key of ['profile', 'notifications', 'experience', 'kiosk', 'modules', 'dashboard', 'apikeys', 'ha']) {
      expect_(key, true);
    }
    // smart home
    expect_('ha-publish', gates.smartHomeEnabled);
    // instance management
    expect_('storage', gates.canManageInstanceSettings);
    expect_('weather-providers', gates.canManageInstanceSettings);
    expect_('plant-identification', gates.canManageInstanceSettings);
    expect_('recognition', gates.canManageInstanceSettings);
    // the HA connection keeps both of its former conditions
    expect_('ha-connection', gates.canManageInstanceSettings && gates.smartHomeEnabled);
  });

  it.each(MATRIX)('shows the Installation group to operators only, and no empty group (%o)', (gates) => {
    const groups = resolveVisibleSettingsGroups(gates);
    expect(groups.some((g) => g.key === 'installation')).toBe(gates.canManageInstanceSettings);
    for (const group of groups) expect(group.sections.length, group.key).toBeGreaterThan(0);
  });
});
