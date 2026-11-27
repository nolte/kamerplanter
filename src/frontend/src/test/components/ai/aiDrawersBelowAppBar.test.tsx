import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import i18n from 'i18next';
import type { ReactElement } from 'react';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import { KioskProvider } from '@/kiosk/KioskProvider';
import { createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * #3162 — the KI drawers ("Warum?" and the chat) start below a bar stacked above them and carry a close button.
 *
 * Both are page-level drawers (`WhyButton`, `KIAssistentPage`) of routes under `MainLayout`, which renders its
 * routes into the standard shell or, while kiosk mode is on, into the kiosk shell. Each case is measured in the
 * shell it can appear in: the stacking of the bar decides whether the paper needs the offset.
 */

// Light mode keeps KioskProvider from attempting a server preference sync, as in MainLayout.kiosk.test.tsx.
vi.mock('@/config/mode', () => ({
  isLightMode: true,
  isFullMode: false,
  KAMERPLANTER_MODE: 'light',
}));

// The drawers load on open; a request that never settles keeps them in their loading state, which is not under test.
vi.mock('@/api', () => ({
  aiApi: {
    explain: vi.fn(() => new Promise(() => undefined)),
    createConversation: vi.fn(() => new Promise(() => undefined)),
  },
}));

import WhyDrawer from '@/components/ai/WhyDrawer';
import AiChatDrawer from '@/components/ai/AiChatDrawer';

const KIOSK_ON = { 'kp-kiosk-preference': JSON.stringify({ kiosk_enabled: true, high_contrast: true }) };

function stubLocalStorage(seed?: Record<string, string>) {
  const store = new Map<string, string>(Object.entries(seed ?? {}));
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
}

interface DrawerCase {
  name: string;
  testId: string;
  closeTestId: string;
  width: number;
  render: (onClose: () => void) => ReactElement;
}

const CASES: DrawerCase[] = [
  {
    name: 'WhyDrawer',
    testId: 'why-drawer',
    closeTestId: 'why-drawer-close',
    width: 360,
    render: (onClose) => (
      <WhyDrawer
        open
        onClose={onClose}
        request={{ subject_type: 'task', subject_key: 't-1', question_template_id: 'task_explain' }}
      />
    ),
  },
  {
    name: 'AiChatDrawer',
    testId: 'ai-chat-drawer',
    closeTestId: 'ai-chat-drawer-close',
    width: 420,
    render: (onClose) => <AiChatDrawer open onClose={onClose} />,
  },
];

/** The drawer as a page of `MainLayout`, the shell both of its users sit in. */
function renderInShell(drawer: ReactElement) {
  const router = createMemoryRouter([{ element: <MainLayout />, children: [{ path: '/page', element: drawer }] }], {
    initialEntries: ['/page'],
  });
  render(
    <Provider store={createTestStore()}>
      <KioskProvider>
        <ThemeContextProvider>
          <RouterProvider router={router} />
        </ThemeContextProvider>
      </KioskProvider>
    </Provider>,
  );
}

const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const emittedCss = () => [...document.querySelectorAll('style')].map((s) => s.textContent).join('\n');
const cssClass = (element: Element) => [...element.classList].find((c) => /^css-/.test(c))!;
const zIndex = (element: Element) => Number(window.getComputedStyle(element).zIndex);

function paperOf(drawer: HTMLElement): HTMLElement {
  return drawer.querySelector('.MuiDrawer-paper') as HTMLElement;
}

/** The responsive width must survive next to the offset's media queries (the defect of #3161). */
function expectWidthKept(paper: HTMLElement, width: number) {
  const css = emittedCss();
  const paperClass = cssClass(paper);
  expect(css).toContain(`@media (min-width:0px){.${paperClass}{width:100%;}`);
  expect(css).toContain(`@media (min-width:600px){.${paperClass}{width:${width}px;}`);
}

describe.each(CASES)('$name (#3162)', ({ testId, closeTestId, width, render: renderDrawer }) => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('starts below the standard app bar that lies above it, its width kept', async () => {
    stubLocalStorage();
    renderInShell(renderDrawer(() => undefined));

    const drawer = await screen.findByTestId(testId);
    const paper = paperOf(drawer);
    // Queried directly: the open modal drawer hides the rest of the page from the accessibility tree.
    const bar = document.querySelector('header.MuiAppBar-root') as HTMLElement;
    const toolbar = bar.querySelector('.MuiToolbar-root') as HTMLElement;

    // The reason for the offset: the bar is stacked above the drawer.
    expect(zIndex(bar)).toBeGreaterThan(zIndex(drawer));
    const barHeight = window.getComputedStyle(toolbar).minHeight;
    expect(barHeight).toBe('56px');
    expect(window.getComputedStyle(paper).top).toBe(barHeight);
    expect(window.getComputedStyle(paper).height).toBe(`calc(100% - ${barHeight})`);

    const css = emittedCss();
    const paperClass = cssClass(paper);
    const toolbarClass = cssClass(toolbar);
    for (const media of ['@media (min-width:600px)', '@media (min-width:0px){@media (orientation: landscape)']) {
      const toolbarRule = new RegExp(`${escape(media)}\\{\\.${toolbarClass}\\{min-height:(\\d+px);\\}`).exec(css);
      expect(toolbarRule, `the bar's height under ${media}`).not.toBeNull();
      const height = toolbarRule![1];
      expect(css).toContain(`${media}{.${paperClass}{top:${height};height:calc(100% - ${height});}`);
    }
    expectWidthKept(paper, width);
  });

  it('covers the kiosk bar from the top instead: no offset in the kiosk shell, its width kept', async () => {
    stubLocalStorage(KIOSK_ON);
    renderInShell(renderDrawer(() => undefined));

    const drawer = await screen.findByTestId(testId);
    const paper = paperOf(drawer);
    // The kiosk shell is its own lazy chunk: the drawer renders inside it once it has arrived.
    const bar = await screen.findByTestId('kiosk-app-bar');

    // The kiosk bar keeps MUI's app bar level, below the drawer's: the drawer's header is not hidden under it.
    expect(zIndex(drawer)).toBeGreaterThan(zIndex(bar));
    expect(window.getComputedStyle(paper).top).toMatch(/^0(px)?$/);
    expect(emittedCss()).not.toMatch(new RegExp(`\\.${cssClass(paper)}\\{top:\\d`));
    expectWidthKept(paper, width);
  });

  it('carries a named close button top right that calls onClose; Escape still closes', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(renderDrawer(onClose));

    const drawer = await screen.findByTestId(testId);
    const close = within(drawer).getByTestId(closeTestId);
    expect(close).toHaveAccessibleName('Schließen');
    expect(close.tagName).toBe('BUTTON');

    await user.click(close);
    expect(onClose).toHaveBeenCalledTimes(1);

    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});

describe('AiChatDrawer content (#3162)', () => {
  afterEach(() => cleanup());

  it('fills the shortened paper instead of taking 100% height, so the input row stays inside it', async () => {
    renderWithProviders(<AiChatDrawer open onClose={() => undefined} />);
    const region = await screen.findByRole('region', { name: 'KI-Chat' });
    const regionClass = cssClass(region);
    const rule = new RegExp(`\\.${regionClass}\\{([^}]*)\\}`).exec(emittedCss())![1];
    expect(rule).toContain('flex:1');
    expect(rule).toContain('min-height:0');
    expect(rule).not.toContain('height:100%');
    expect(within(region).getByTestId('ai-chat-input')).toBeInTheDocument();
  });
});
