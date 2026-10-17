import path from 'node:path';
import { ESLint } from 'eslint';
import { describe, expect, it } from 'vitest';

/**
 * GP-NFR-009: the editor (`features/gardenPlanner/editor/**`) imports the `PlanRenderer` interface
 * and never a renderer implementation or rendering library, so Konva can be swapped in (D-01).
 * The rule lives in `eslint.config.js`; this test lints fixture sources against the real config.
 */
const ROOT = path.resolve(__dirname, '../../..');
const EDITOR_FILE = path.join(ROOT, 'src/features/gardenPlanner/editor/tools/someTool.ts');
const ROUTE_FILE = path.join(ROOT, 'src/features/gardenPlanner/routes/GardenPlanRoute.ts');

async function restrictedImports(code: string, filePath: string): Promise<string[]> {
  const eslint = new ESLint({ cwd: ROOT });
  const [result] = await eslint.lintText(code, { filePath });
  return result.messages.filter((m) => m.ruleId === 'no-restricted-imports').map((m) => m.message);
}

describe('gardenPlanner editor/** may import only the PlanRenderer interface', () => {
  it.each([
    ["import { SvgPlanRenderer } from '../../renderer/SvgPlanRenderer';"],
    ["import { SvgPlanRenderer } from '@/features/gardenPlanner/renderer/SvgPlanRenderer';"],
    ["import { x } from '../../renderer/svg/internals';"],
    ["import Konva from 'konva';"],
    ["import { Stage } from 'react-konva';"],
    ["import { fabric } from 'fabric';"],
  ])('rejects %s', async (code) => {
    const messages = await restrictedImports(`${code}\nexport const used = 1;\n`, EDITOR_FILE);
    expect(messages).not.toEqual([]);
  });

  it('accepts the interface and the headless double', async () => {
    const code = [
      "import type { PlanRenderer } from '../../renderer';",
      "import type { Viewport } from '../../renderer/types';",
      "import { HeadlessPlanRenderer } from '../../renderer/HeadlessPlanRenderer';",
      'export type Used = [PlanRenderer, Viewport, typeof HeadlessPlanRenderer];',
    ].join('\n');
    expect(await restrictedImports(code, EDITOR_FILE)).toEqual([]);
  });

  it('does not restrict the code that wires the renderer in (outside editor/**)', async () => {
    const code =
      "import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';\nexport const r = SvgPlanRenderer;\n";
    expect(await restrictedImports(code, ROUTE_FILE)).toEqual([]);
  });
});
