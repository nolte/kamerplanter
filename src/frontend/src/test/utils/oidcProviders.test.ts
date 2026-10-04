import { describe, it, expect } from 'vitest';
import type { OidcProvider } from '@/api/types';
import { githubScopesLackEmail, oidcUpdateNeedsStepUp, parseScopes } from '@/utils/oidcProviders';

/**
 * #1906 — the page opens the step-up first exactly when the backend will ask for it
 * (`update_requires_step_up`, operator decision D6, SEC-001): presentation fields are free,
 * everything else — including switching on **or off** and any client secret — is not.
 */
const CURRENT: OidcProvider = {
  key: 'k1',
  slug: 'kc',
  display_name: 'Keycloak',
  provider_type: 'oidc',
  issuer_url: 'https://id.example/realms/home',
  client_id: 'kamerplanter',
  scopes: ['openid', 'email', 'profile'],
  enabled: true,
  icon_url: null,
  auto_discover: true,
  discovery_refreshed_at: null,
  created_at: null,
  updated_at: null,
};

describe('oidcUpdateNeedsStepUp', () => {
  it.each([
    ['display name', { display_name: 'Neu' }],
    ['icon set', { icon_url: 'https://cdn.example/i.png' }],
    ['icon cleared', { icon_url: '' }],
    ['both presentation fields', { display_name: 'Neu', icon_url: 'https://cdn.example/i.png' }],
    ['a value equal to the stored one', { issuer_url: CURRENT.issuer_url }],
    ['equal scopes', { scopes: ['openid', 'email', 'profile'] }],
  ])('needs none for %s', (_name, payload) => {
    expect(oidcUpdateNeedsStepUp(CURRENT, payload)).toBe(false);
  });

  it.each([
    ['issuer', { issuer_url: 'https://evil.example' }],
    ['provider type', { provider_type: 'github' as const }],
    ['client id', { client_id: 'other' }],
    ['scopes', { scopes: ['openid'] }],
    ['switching off', { enabled: false }],
    ['auto discover', { auto_discover: false }],
    ['a client secret, always', { client_secret: 'whatever' }],
    ['presentation mixed with a sign-in field', { display_name: 'Neu', enabled: false }],
  ])('needs it for %s', (_name, payload) => {
    expect(oidcUpdateNeedsStepUp(CURRENT, payload)).toBe(true);
  });

  it('switching ON also needs it (the mirror of switching off)', () => {
    expect(oidcUpdateNeedsStepUp({ ...CURRENT, enabled: false }, { enabled: true })).toBe(true);
  });
});

describe('parseScopes', () => {
  it('splits on spaces and commas, drops empties, keeps order', () => {
    expect(parseScopes(' openid,email  profile ,, ')).toEqual(['openid', 'email', 'profile']);
    expect(parseScopes('')).toEqual([]);
  });
});

describe('githubScopesLackEmail', () => {
  it.each([
    [['read:user'], true],
    [['user:email'], false],
    [['user'], false],
    [['read:user user:email'], false],
    [['USER:EMAIL'], true],
  ])('%j → lacks %s', (scopes, lacks) => {
    expect(githubScopesLackEmail(scopes)).toBe(lacks);
  });
});
