import client from '../client';
import type { CalendarEventsResponse, CalendarFeed } from '../types';

export async function getCalendarEvents(
  start: string,
  end: string,
  category?: string,
  tenantKey?: string,
): Promise<CalendarEventsResponse> {
  const params: Record<string, string> = { start, end };
  if (category) params.category = category;
  if (tenantKey) params.tenant_key = tenantKey;
  const response = await client.get<CalendarEventsResponse>('/calendar/events', { params });
  return response.data;
}

export async function createCalendarFeed(
  name: string,
  filters: { categories: string[]; site_key: string | null },
): Promise<CalendarFeed> {
  const response = await client.post<CalendarFeed>('/calendar/feeds', { name, filters });
  return response.data;
}

export async function listCalendarFeeds(
  userKey?: string,
  tenantKey?: string,
): Promise<CalendarFeed[]> {
  const params: Record<string, string> = {};
  if (userKey) params.user_key = userKey;
  if (tenantKey) params.tenant_key = tenantKey;
  const response = await client.get<CalendarFeed[]>('/calendar/feeds', { params });
  return response.data;
}

export async function getCalendarFeed(key: string): Promise<CalendarFeed> {
  const response = await client.get<CalendarFeed>(`/calendar/feeds/${key}`);
  return response.data;
}

export async function updateCalendarFeed(
  key: string,
  body: { name: string; filters: { categories: string[]; site_key: string | null }; is_active: boolean },
): Promise<CalendarFeed> {
  const response = await client.put<CalendarFeed>(`/calendar/feeds/${key}`, body);
  return response.data;
}

export async function deleteCalendarFeed(key: string): Promise<void> {
  await client.delete(`/calendar/feeds/${key}`);
}

export async function regenerateCalendarFeedToken(key: string): Promise<CalendarFeed> {
  const response = await client.post<CalendarFeed>(`/calendar/feeds/${key}/regenerate-token`);
  return response.data;
}
