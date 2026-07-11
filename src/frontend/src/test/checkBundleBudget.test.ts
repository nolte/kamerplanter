import { describe, it, expect } from 'vitest';
// The budget gate script is authored as an .mjs Node CLI; Vitest can import its
// pure, side-effect-free export directly (the CLI `main()` is guarded by an
// import.meta.url check, so importing it does not run the build measurement).
import { evaluateBudget, kib } from '../../scripts/check-bundle-budget.mjs';

/**
 * UI-NFR-003 R-013/R-014/R-015/R-028 — unit coverage for the bundle-budget
 * evaluation logic that decides whether CI fails. Exercises the pass path, the
 * hard-fail path (initial JS over budget), the CSS warn severity, and the
 * dedicated /dashboard route-chunk budget.
 */
const budget = {
  initialJsGzipKb: 490,
  initialCssGzipKb: 50,
  cssSeverity: 'error' as const,
  routeChunks: { dashboard: { source: 'src/pages/DashboardPage.tsx', gzipKb: 12 } },
};

const KB = 1024;

describe('evaluateBudget', () => {
  it('passes when every measured payload is within budget', () => {
    const { checks, failed } = evaluateBudget({
      initialJsBytes: 400 * KB,
      initialCssBytes: 1 * KB,
      dashboardBytes: 3 * KB,
      budget,
    });
    expect(failed).toBe(false);
    expect(checks.every((c) => c.status === 'PASS')).toBe(true);
  });

  it('fails hard when the initial JS exceeds its budget (R-015)', () => {
    const { checks, failed } = evaluateBudget({
      initialJsBytes: 600 * KB,
      initialCssBytes: 1 * KB,
      dashboardBytes: 3 * KB,
      budget,
    });
    expect(failed).toBe(true);
    const jsCheck = checks.find((c) => c.requirement === 'R-013/R-015');
    expect(jsCheck?.status).toBe('FAIL');
  });

  it('fails when the /dashboard route chunk exceeds its dedicated budget (R-028)', () => {
    const { checks, failed } = evaluateBudget({
      initialJsBytes: 400 * KB,
      initialCssBytes: 1 * KB,
      dashboardBytes: 20 * KB,
      budget,
    });
    expect(failed).toBe(true);
    const dashCheck = checks.find((c) => c.requirement === 'R-028');
    expect(dashCheck?.status).toBe('FAIL');
  });

  it('omits the dashboard check when no route chunk is measured', () => {
    const { checks } = evaluateBudget({
      initialJsBytes: 400 * KB,
      initialCssBytes: 1 * KB,
      dashboardBytes: null,
      budget,
    });
    expect(checks.find((c) => c.requirement === 'R-028')).toBeUndefined();
  });

  it('treats a CSS overshoot as a non-blocking warning when cssSeverity is warn', () => {
    const warnBudget = { ...budget, cssSeverity: 'warn' as const };
    const { checks, failed } = evaluateBudget({
      initialJsBytes: 400 * KB,
      initialCssBytes: 60 * KB,
      dashboardBytes: 3 * KB,
      budget: warnBudget,
    });
    expect(failed).toBe(false);
    const cssCheck = checks.find((c) => c.requirement === 'R-014');
    expect(cssCheck?.status).toBe('WARN');
  });

  it('formats byte counts as KB', () => {
    expect(kib(1024)).toBe('1.0 KB');
    expect(kib(1536)).toBe('1.5 KB');
  });
});
