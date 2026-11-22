import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  buildNotification,
  parsePushData,
  resolveTargetUrl,
  toSafeSameOriginPath,
} from '@/pwa/pushHandlers';

/**
 * REQ-053 WP 9.1 (#2741) — Web-Push regression fence. The Workbox worker built from `src/sw.ts`
 * replaced the hand-written `public/sw.js` and took over its push handlers. If the handlers went
 * missing, every push would arrive at a worker that ignores it — silently, because nothing in the
 * app fails. Both workers must never coexist: the build emits `/sw.js` from `src/sw.ts`, and a
 * `public/sw.js` would be copied over it (or beside it under another name).
 *
 * UI-NFR-012 R-011: the one worker is built by `vite-plugin-pwa` in `injectManifest` mode from `src/sw.ts`.
 */

const root = process.cwd();
const swSource = readFileSync(join(root, 'src/sw.ts'), 'utf8');

describe('src/sw.ts carries the Web Push handlers', () => {
  it('listens for push and shows a notification built by the shared helper', () => {
    expect(swSource).toMatch(/self\.addEventListener\('push',/);
    const push = swSource.slice(swSource.indexOf("self.addEventListener('push'"));
    expect(push).toMatch(/buildNotification\(parsePushData\(event\.data\)\)/);
    expect(push).toMatch(/event\.waitUntil\(self\.registration\.showNotification\(title,/);
  });

  it('handles notification clicks through the same-origin URL guard', () => {
    expect(swSource).toMatch(/self\.addEventListener\('notificationclick',/);
    const click = swSource.slice(swSource.indexOf("self.addEventListener('notificationclick'"));
    expect(click).toMatch(/resolveTargetUrl\(event\.notification\.data, event\.action, self\.location\.origin\)/);
    expect(click).toMatch(/openWindow\(targetUrl\)/);
  });

  it('is the only worker: public/sw.js is gone and the build emits sw.ts as /sw.js', () => {
    expect(existsSync(join(root, 'public/sw.js'))).toBe(false);
    const viteConfig = readFileSync(join(root, 'vite.config.ts'), 'utf8');
    expect(viteConfig).toMatch(/strategies: 'injectManifest'/);
    expect(viteConfig).toMatch(/filename: 'sw\.ts'/);
    const registration = readFileSync(join(root, 'src/lib/serviceWorkerRegistration.ts'), 'utf8');
    expect(registration).toMatch(/url: '\/sw\.js', type: 'classic'/);
  });
});

describe('push payload handling', () => {
  const origin = 'https://kamerplanter.example';

  it('builds a notification from the JSON payload with safe defaults', () => {
    const payload = parsePushData({
      json: () => ({ title: 'Gießen', body: 'Beet 3', tag: 'care', data: { url: '/pflege' } }),
      text: () => '',
    });
    const { title, options } = buildNotification(payload);
    expect(title).toBe('Gießen');
    expect(options).toMatchObject({ body: 'Beet 3', tag: 'care', renotify: true, data: { url: '/pflege' } });
    expect(options.icon).toBe('/icons/icon-192.png');
  });

  it('never throws on a malformed push', () => {
    expect(parsePushData(null)).toEqual({});
    const textOnly = parsePushData({
      json: () => {
        throw new Error('not json');
      },
      text: () => 'plain',
    });
    expect(buildNotification(textOnly)).toMatchObject({ title: 'Kamerplanter', options: { body: 'plain' } });
  });

  it('never navigates cross-origin from a notification click', () => {
    expect(toSafeSameOriginPath('https://evil.example/phish', origin)).toBe('/');
    expect(toSafeSameOriginPath('javascript:alert(1)', origin)).toBe('/');
    expect(toSafeSameOriginPath('//evil.example/x', origin)).toBe('/');
    expect(toSafeSameOriginPath('/aufgaben?x=1#a', origin)).toBe('/aufgaben?x=1#a');
    expect(resolveTargetUrl({ action_urls: { open: '/pflege' }, url: '/x' }, 'open', origin)).toBe('/pflege');
    expect(resolveTargetUrl({ url: 'https://evil.example' }, undefined, origin)).toBe('/');
    expect(resolveTargetUrl(null, undefined, origin)).toBe('/');
  });
});
