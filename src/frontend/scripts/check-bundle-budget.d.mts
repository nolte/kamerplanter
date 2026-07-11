// Type declarations for the Node-side bundle-budget gate so its pure exports can
// be imported from Vitest specs under TypeScript strict mode.

export interface BudgetRouteChunk {
  source: string;
  gzipKb: number;
}

export interface BundleBudgetConfig {
  initialJsGzipKb: number;
  initialCssGzipKb: number;
  cssSeverity?: 'error' | 'warn';
  routeChunks: {
    dashboard: BudgetRouteChunk;
  };
}

export interface BudgetCheck {
  label: string;
  requirement: string;
  actual: number;
  budget: number;
  severity: 'error' | 'warn';
  over: boolean;
  status: 'PASS' | 'WARN' | 'FAIL';
}

export interface EvaluateBudgetInput {
  initialJsBytes: number;
  initialCssBytes: number;
  dashboardBytes: number | null | undefined;
  budget: BundleBudgetConfig;
}

export function evaluateBudget(input: EvaluateBudgetInput): {
  checks: BudgetCheck[];
  failed: boolean;
};

export function kib(bytes: number): string;
