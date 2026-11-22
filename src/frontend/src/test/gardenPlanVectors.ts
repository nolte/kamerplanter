/// <reference types="node" />
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Loader of the shared geometry vectors (REQ-053 §19.6) for the tests of this feature.
 *
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json` is the single source of truth of the
 * Backend <-> Frontend geometry logic: the Python reference test and the TypeScript port test read
 * this same file. The file is required, not optional - an unreachable checkout root throws instead
 * of skipping, because a silently skipped SSOT test is a vector file nobody runs. Test support
 * only: nothing in the app imports this module.
 */
const VECTOR_PATH = join('spec', 'e2e-testcases', 'fixtures', 'garden-plan-vectors.json');

export interface VectorCase {
  id: string;
  operation: string;
  spec: string;
  input: Record<string, unknown>;
  expected: unknown;
  tolerance?: number;
}

export interface VectorFile {
  format_version: number;
  default_tolerance: number;
  operations: Record<string, string>;
  cases: VectorCase[];
}

function findVectorFile(): string {
  let directory = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    const candidate = join(directory, VECTOR_PATH);
    if (existsSync(candidate)) return candidate;
    const parent = dirname(directory);
    if (parent === directory) {
      throw new Error(`checkout root not found; ${VECTOR_PATH} is unreachable from here`);
    }
    directory = parent;
  }
}

export function loadVectors(): VectorFile {
  return JSON.parse(readFileSync(findVectorFile(), 'utf-8')) as VectorFile;
}
