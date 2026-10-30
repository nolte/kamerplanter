import path from 'node:path';
import { ESLint } from 'eslint';
import { describe, expect, it } from 'vitest';

/**
 * #2518: `src/features/**` never depends on `src/pages/**` — not by a static import, a re-export,
 * a type import, a dynamic `import()` (string or template literal), nor a vitest module call
 * (`vi.mock` / `vi.importActual` ...). The rule lives in `eslint.config.js`; this test lints
 * fixture sources against the real config. The garden editor block re-declares
 * `no-restricted-imports` (GP-NFR-009), which replaces the features block's options for those
 * files, so every case runs for a plain feature file AND for an editor file.
 */
const ROOT = path.resolve(__dirname, '../../..');
const FEATURE_FILE = path.join(ROOT, 'src/features/x/y.ts');
const EDITOR_FILE = path.join(ROOT, 'src/features/gardenPlanner/editor/tools/t.ts');
const EDITOR_TSX_FILE = path.join(ROOT, 'src/features/gardenPlanner/editor/tools/t.tsx');
const FEATURE_TEST_FILE = path.join(ROOT, 'src/features/x/y.test.ts');

const PAGES_MESSAGE = 'src/features must not import from src/pages (#2518).';

interface Report {
  ruleId: string | null;
  message: string;
}

async function lint(code: string, filePath: string): Promise<Report[]> {
  const eslint = new ESLint({ cwd: ROOT });
  const [result] = await eslint.lintText(code, { filePath });
  return result.messages.map((m) => ({ ruleId: m.ruleId, message: m.message }));
}

async function pagesReports(code: string, filePath: string): Promise<Report[]> {
  return (await lint(code, filePath)).filter((r) => r.message.includes(PAGES_MESSAGE));
}

const REJECTED: [string, string][] = [
  ['static default import via alias', "import A from '@/pages/x';\nexport const used = A;\n"],
  [
    'static default import via ../ chain',
    "import A from '../../pages/x';\nexport const used = A;\n",
  ],
  ['star re-export', "export * from '@/pages/x';\n"],
  ['type-only import', "import type { T } from '@/pages/x';\nexport type Used = T;\n"],
  [
    'lazy dynamic import',
    "import { lazy } from 'react';\nexport const L = lazy(() => import('@/pages/x'));\n",
  ],
  [
    'dynamic import of a template literal',
    'export const load = (n: string) => import(`../../pages/${n}`);\n',
  ],
];

const ACCEPTED: [string, string][] = [
  [
    'the i18n pages.json namespace',
    'export const load = (l: string) => import(`../../../i18n/locales/${l}/pages.json`);\n',
  ],
  [
    'a component name containing "pages"',
    "import A from '@/components/pages-foo';\nexport const used = A;\n",
  ],
  [
    'a feature-local module named pagesUtil',
    "import A from './pagesUtil';\nexport const used = A;\n",
  ],
];

describe.each([
  ['src/features/x/y.ts', FEATURE_FILE],
  ['src/features/gardenPlanner/editor/tools/t.ts', EDITOR_FILE],
])('features must not import from pages — %s', (_label, filePath) => {
  it.each(REJECTED)('rejects a %s', async (_name, code) => {
    expect(await pagesReports(code, filePath)).not.toEqual([]);
  });

  it.each(ACCEPTED)('accepts %s', async (_name, code) => {
    expect(await pagesReports(code, filePath)).toEqual([]);
  });
});

describe('features must not reach pages through vitest module calls', () => {
  it.each([
    ["vi.mock('@/pages/x');\n"],
    ["export const actual = await vi.importActual('@/pages/x');\n"],
    ["vi.doMock('../../pages/x');\n"],
    ["export const mocked = await vi.importMock('@/pages/x');\n"],
  ])('rejects %s', async (code) => {
    const src = `import { vi } from 'vitest';\n${code}`;
    expect(await pagesReports(src, FEATURE_TEST_FILE)).not.toEqual([]);
  });

  it('accepts a vitest mock of a non-page module', async () => {
    const src = "import { vi } from 'vitest';\nvi.mock('@/components/pages-foo');\n";
    expect(await pagesReports(src, FEATURE_TEST_FILE)).toEqual([]);
  });
});

describe('the #2518 rule does not displace earlier rules in the editor', () => {
  it('still reports a raw <form> (#825)', async () => {
    const code = 'export const F = () => <form onSubmit={() => undefined} />;\n';
    const reports = await lint(code, EDITOR_TSX_FILE);
    expect(
      reports.some((r) => r.ruleId === 'no-restricted-syntax' && r.message.includes('#825')),
    ).toBe(true);
  });

  it('still reports a rendering library (GP-NFR-009)', async () => {
    const code = "import Konva from 'konva';\nexport const used = Konva;\n";
    const reports = await lint(code, EDITOR_FILE);
    expect(
      reports.some((r) => r.ruleId === 'no-restricted-imports' && r.message.includes('GP-NFR-009')),
    ).toBe(true);
  });
});
