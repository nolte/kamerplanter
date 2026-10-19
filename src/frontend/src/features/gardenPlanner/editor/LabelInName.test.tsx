/**
 * WCAG 2.5.3 Label in Name for the toggles of the plan editor (#2388, GP-ACC-032): a button that
 * shows text must carry that text in its accessible name, or a speech-input user who says what
 * they see ("click cm") cannot reach it. axe cannot check this here: the tool short text is only
 * displayed from `lg` up, and jsdom lays out no breakpoint. So the DOM is read directly, with the
 * short text present, and compared the way axe's `label-content-name-mismatch` does (axe-core
 * >= 4.11, `isLabelContainedInName`): lower case, parenthesised text REMOVED from both sides, then
 * the visible words must be a contiguous run of the name's words. "Zentimeter (cm)" therefore
 * does not contain "cm" (#2497: the first fix of #2388 used that form and stayed red in the E2E).
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import i18n from '@/i18n/i18n';
import { ThemeContextProvider } from '@/theme';
import { EditorToolbar } from './EditorToolbar';
import { ViewBar } from './ViewBar';

const words = (text: string): string[] => {
  let previous: string;
  let stripped = text.toLowerCase();
  do {
    previous = stripped;
    stripped = stripped.replace(/\([^()]*\)/g, '');
  } while (stripped !== previous);
  return stripped.split(/[^\p{L}\p{N}]+/u).filter(Boolean);
};

const containsRun = (haystack: string[], needle: string[]): boolean =>
  needle.length === 0 ||
  haystack.some((_, start) => needle.every((word, offset) => haystack[start + offset] === word));

function labelInNameViolations(root: HTMLElement): string[] {
  const broken: string[] = [];
  for (const button of root.querySelectorAll<HTMLElement>('button[aria-label]')) {
    const visible = (button.textContent ?? '').trim();
    if (!visible) continue;
    const name = words(button.getAttribute('aria-label') ?? '');
    if (!containsRun(name, words(visible))) {
      broken.push(
        `${button.getAttribute('data-testid') ?? button.outerHTML}: text "${visible}", name "${button.getAttribute('aria-label')}"`,
      );
    }
  }
  return broken;
}

function renderBars() {
  render(
    <ThemeContextProvider>
      <ViewBar
        gridStepM={0.1}
        onGridStep={() => undefined}
        gridVisible
        onGridVisible={() => undefined}
        snapEnabled
        onSnapEnabled={() => undefined}
        pxPerM={40}
        minPxPerM={10}
        onZoomIn={() => undefined}
        onZoomOut={() => undefined}
        onFit={() => undefined}
        unit="cm"
        onUnit={() => undefined}
        northAngleDeg={0}
      />
      <EditorToolbar
        tool="select"
        onTool={() => undefined}
        drawShape="rect"
        onDrawShape={() => undefined}
        angleStep={15}
        onAngleStep={() => undefined}
        draftPoints={0}
        onFinishDraw={() => undefined}
        onCancelDraw={() => undefined}
        canDelete={false}
        onDelete={() => undefined}
        vertexPicked={false}
        canDeleteVertex={false}
        onDeleteVertex={() => undefined}
        onInsertVertex={() => undefined}
      />
    </ThemeContextProvider>,
  );
}

const original = i18n.language;
beforeEach(() => cleanup());
afterEach(async () => {
  cleanup();
  await i18n.changeLanguage(original);
});

describe('label in name matcher', () => {
  it('rejects a name that only holds the visible text in parentheses (axe drops it)', () => {
    const button = document.createElement('div');
    button.innerHTML = '<button aria-label="Zentimeter (cm)">cm</button><button aria-label="cm: Zentimeter">cm</button>';
    expect(labelInNameViolations(button)).toHaveLength(1);
  });
});

describe('label in name of the editor toggles (WCAG 2.5.3, #2388)', () => {
  it.each(['de', 'en'])('every toggle with visible text names that text (%s)', async (language) => {
    await i18n.changeLanguage(language);
    renderBars();
    // The short form is in the DOM (only hidden by CSS below lg): the guard really looks at it.
    expect(screen.getByTestId('garden-plan-tool-garden_object')).toHaveTextContent(/\S/);
    expect(screen.getByTestId('garden-plan-unit-cm')).toHaveTextContent('cm');
    expect(labelInNameViolations(document.body)).toEqual([]);
  });
});
