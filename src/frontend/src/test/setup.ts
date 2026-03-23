import '@testing-library/jest-dom/vitest';
import 'vitest-axe/extend-expect';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { server } from './mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import '@/i18n';

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
