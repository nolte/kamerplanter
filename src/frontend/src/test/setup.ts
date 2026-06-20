import '@testing-library/jest-dom/vitest';
import 'vitest-axe/extend-expect';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { server } from './mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import '@/i18n';

// jsdom does not implement the Object-URL APIs that AuthImage (and any blob-based
// rendering) relies on. Provide deterministic stubs so components can create and
// revoke Object-URLs in tests without touching the real (absent) implementation.
if (typeof URL.createObjectURL !== 'function') {
  let counter = 0;
  URL.createObjectURL = () => `blob:mock/${++counter}`;
}
if (typeof URL.revokeObjectURL !== 'function') {
  URL.revokeObjectURL = () => undefined;
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
