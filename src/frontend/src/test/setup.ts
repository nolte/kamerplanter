import '@testing-library/jest-dom/vitest';
import 'vitest-axe/extend-expect';
import { cleanup, configure } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { server } from './mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import '@/i18n';
import { loadFeatureNamespacesForTests } from './i18nTestResources';

// #612 — register the code-split feature namespaces synchronously so every
// `t()` key resolves in tests without awaiting a dynamic import.
loadFeatureNamespacesForTests();

// Raise Testing-Library's async-utility timeout above the 1000ms default. Under
// full-suite parallelism the workers contend for CPU, so an async `findBy*` /
// `waitFor` that resolves comfortably in an isolated run can miss the 1s window
// and produce a wandering, load-dependent failure that never reproduces in
// isolation. A larger ceiling only extends the *maximum* wait on the failure
// path; passing assertions still resolve as soon as the element appears.
configure({ asyncUtilTimeout: 5000 });

// jsdom does not implement the Object-URL APIs that AuthImage (and any blob-based
// rendering) relies on. Provide deterministic stubs so components can create and
// revoke Object-URLs in tests without touching the real (absent) implementation.
//
// Set UNCONDITIONALLY (not only when missing): under Node 22 the test environment
// ships a native createObjectURL that rejects anything that is not a structurally
// real Blob, while the axios/undici blob response is not always a real Blob across
// Node versions. That made createObjectURL throw -> useAuthImage fell into its
// catch -> the image never rendered -> findByTestId timed out, but only on Node 22
// (CI), not Node 25 (local). A deterministic stub removes the Node dependency.
{
  let counter = 0;
  URL.createObjectURL = () => `blob:mock/${++counter}`;
  URL.revokeObjectURL = () => undefined;
}

// jsdom's Blob has no `stream()` (only slice/text/arrayBuffer/bytes). The MSW
// XMLHttpRequest interceptor wraps every mocked response in a fetch `Response`,
// and for an axios request with `responseType: 'blob'` that body is a jsdom
// Blob. Node 22's bundled undici 6 duck-types the body as Blob-like and calls
// `.stream()` on it -> `TypeError: object.stream is not a function` as an
// unhandled rejection inside the interceptor, before the XHR `load` event
// fires -> the axios promise never settles and the component under test never
// reaches its download hand-over. Node 25's undici 7 takes a different path,
// so the failure is CI-only (#1645, PR #1662). Browsers implement
// `Blob.prototype.stream`; giving jsdom's the same shape removes the Node
// dependency without touching the component.
if (typeof Blob.prototype.stream !== 'function') {
  Blob.prototype.stream = function stream(this: Blob): ReadableStream<Uint8Array<ArrayBuffer>> {
    const bytes = this.arrayBuffer();
    return new ReadableStream<Uint8Array<ArrayBuffer>>({
      async pull(controller) {
        controller.enqueue(new Uint8Array(await bytes));
        controller.close();
      },
    });
  };
}

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});
beforeEach(() => {
  // Set tenant slug for tenantClient before each test
  setActiveTenantSlug('test-tenant');
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
