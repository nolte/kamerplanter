import axios from 'axios';
import { ApiError } from './errors';
import type { ApiErrorResponse } from './types';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const data = error.response.data as ApiErrorResponse;
      if (data?.error_id && data?.error_code) {
        throw new ApiError(data, error.response.status);
      }
    }
    throw error;
  },
);

export default client;
