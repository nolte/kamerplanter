import { describe, it, expect, afterEach, vi } from 'vitest';
import * as Sentry from '@sentry/browser';
import { htmlTreeAsString } from '@sentry/browser-utils';
import { scrubBreadcrumb } from '@/observability/errorTrackingScrub';

/**
 * UI-NFR-013 v1.6 CI-006 d/e (#3025 S-2, N-e) — against the breadcrumbs the
 * INSTALLED SDK actually produces, not a hand-written shape: the console
 * integration keeps the raw arguments in `data.arguments` next to `message`,
 * and a click target is described by `htmlTreeAsString`, including the values of
 * `aria-label`, `title` and `alt`.
 */
describe('breadcrumbs in the shape of the installed SDK', () => {
  afterEach(async () => {
    await Sentry.close(0).catch(() => undefined);
    vi.restoreAllMocks();
  });

  it('drops the raw console arguments and masks the message', async () => {
    const raw: Record<string, unknown>[] = [];
    const sent: Record<string, unknown>[] = [];
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    Sentry.init({
      dsn: 'https://key@tracker.example/1',
      defaultIntegrations: false,
      integrations: [Sentry.consoleIntegration()],
      transport: () => ({
        send: async () => ({}),
        flush: async () => true,
      }),
      beforeBreadcrumb: (crumb) => {
        raw.push(structuredClone(crumb) as unknown as Record<string, unknown>);
        const scrubbed = scrubBreadcrumb(crumb as unknown as Record<string, unknown>);
        if (scrubbed) sent.push(scrubbed);
        return scrubbed as never;
      },
    });

    console.warn(
      'save failed for',
      { name: 'Max Mustermann' },
      '/api/v1/t/max-mustermann/sites/12',
    );

    // Non-vacuity: the SDK really keeps the arguments.
    const original = raw.find((c) => c.category === 'console')!;
    expect((original.data as Record<string, unknown>).arguments).toBeDefined();
    expect(JSON.stringify(original)).toContain('Max Mustermann');

    const crumb = sent.find((c) => c.category === 'console')!;
    expect((crumb.data as Record<string, unknown>).arguments).toBeUndefined();
    expect(JSON.stringify(crumb)).not.toContain('Max Mustermann');
    expect(JSON.stringify(crumb)).not.toContain('max-mustermann');
  });

  it('removes aria-label, title and alt values from a click target description', () => {
    const button = document.createElement('button');
    button.setAttribute('aria-label', 'Berta gießen');
    button.setAttribute('title', 'Max');
    const img = document.createElement('img');
    img.setAttribute('alt', 'Max Foto');
    button.appendChild(img);
    document.body.appendChild(button);
    const message = htmlTreeAsString(img);
    // Non-vacuity: this is what the SDK writes into a ui.click breadcrumb.
    expect(message).toContain('Max Foto');
    expect(message).toContain('Berta gießen');

    const crumb = scrubBreadcrumb({ category: 'ui.click', message })!;

    expect(crumb.message).not.toMatch(/Max|Berta/);
    expect(crumb.message).toContain('[aria-label]');
    expect(crumb.message).toContain('[alt]');
    button.remove();
  });
});
