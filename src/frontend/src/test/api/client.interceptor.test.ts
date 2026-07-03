import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { AxiosError } from 'axios';
import client, { tenantClient } from '@/api/client';
import { ApiError } from '@/api/errors';
import { server } from '../mocks/server';

/**
 * AP-14 (FE-D3): the response interceptor that maps the backend error envelope
 * to a typed {@link ApiError} lives in a single shared `rethrowApiError`
 * function and is wired to both `client` and `tenantClient`. These tests pin the
 * behaviour so a future de-duplication regression is caught.
 */
describe('api client response interceptor', () => {
  const envelope = {
    error_id: 'err_int_1',
    error_code: 'VALIDATION_ERROR',
    message: 'The input data is invalid.',
    details: [],
    timestamp: '2024-01-01T00:00:00Z',
    path: '/api/v1/interceptor-envelope',
    method: 'GET',
  };

  it('converts a backend error envelope into an ApiError (client)', async () => {
    server.use(
      http.get('/api/v1/interceptor-envelope', () =>
        HttpResponse.json(envelope, { status: 422 }),
      ),
    );

    await expect(client.get('/interceptor-envelope')).rejects.toMatchObject({
      errorCode: 'VALIDATION_ERROR',
      statusCode: 422,
      errorId: 'err_int_1',
    });
    await expect(client.get('/interceptor-envelope')).rejects.toBeInstanceOf(ApiError);
  });

  it('converts a backend error envelope into an ApiError (tenantClient)', async () => {
    // tenantClient prepends /t/{slug}; setup.ts sets the active slug to "test-tenant".
    server.use(
      http.get('/api/v1/t/test-tenant/interceptor-envelope', () =>
        HttpResponse.json(envelope, { status: 422 }),
      ),
    );

    await expect(tenantClient.get('/interceptor-envelope')).rejects.toBeInstanceOf(ApiError);
  });

  it('re-throws a non-envelope error unchanged as an AxiosError', async () => {
    server.use(
      http.get('/api/v1/interceptor-raw', () =>
        HttpResponse.json({ detail: 'plain server error' }, { status: 500 }),
      ),
    );

    const rejection = await client.get('/interceptor-raw').catch((e) => e);
    expect(rejection).toBeInstanceOf(AxiosError);
    expect(rejection).not.toBeInstanceOf(ApiError);
    expect(rejection.response?.status).toBe(500);
  });
});
