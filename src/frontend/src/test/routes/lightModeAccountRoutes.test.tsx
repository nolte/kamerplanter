import { describe, it, expect, vi } from 'vitest';
import { isValidElement } from 'react';
import { Navigate, matchRoutes, type RouteObject } from 'react-router-dom';

/**
 * #3025 L-14 — light mode has no accounts, so the account pages are not mounted there. A typed `/login`, an
 * old bookmark or a stale e-mail link used to fall through to the 404 page; each of them now leads to the
 * dashboard. Exercised against the production router, built with the light-mode flag.
 */
vi.mock('@/config/mode', () => ({
  KAMERPLANTER_MODE: 'light',
  isLightMode: true,
  isFullMode: false,
}));

const { router } = await import('@/routes/AppRoutes');

const ACCOUNT_URLS = [
  '/login',
  '/register',
  '/verify-email/abc',
  '/resend-verification',
  '/password-reset',
  '/password-reset/abc',
  '/auth/callback',
  '/auth/step-up/callback',
  '/email-change/abc',
  '/email-change/revert/abc',
  '/privacy',
];

function leafElement(url: string) {
  const matches = matchRoutes(router.routes as RouteObject[], url);
  expect(matches, url).not.toBeNull();
  const leaf = matches![matches!.length - 1].route;
  return leaf;
}

describe('light-mode account routes', () => {
  it.each(ACCOUNT_URLS)('%s redirects to the dashboard instead of the 404 page', (url) => {
    const leaf = leafElement(url);
    expect(leaf.path, url).not.toBe('*');
    const element = leaf.element;
    expect(isValidElement(element), url).toBe(true);
    if (!isValidElement<{ to: string; replace?: boolean }>(element)) return;
    expect(element.type).toBe(Navigate);
    expect(element.props.to).toBe('/dashboard');
    expect(element.props.replace).toBe(true);
  });

  it('still answers an unknown path with the 404 page', () => {
    expect(leafElement('/no-such-page').path).toBe('*');
  });
});
