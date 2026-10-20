import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import type { CareTask } from './careTypes';

/** Fixtures of the care tab tests (REQ-053 WP 4.4). */

export const BASE = '/api/v1/t/:tenant';

export function careTask(key: string, overrides: Partial<CareTask> = {}): CareTask {
  return {
    key,
    name: `Task ${key}`,
    name_de: '',
    instruction: '',
    instruction_de: '',
    category: 'watering',
    origin: 'user',
    source: '',
    source_run_ref: null,
    external_ref: null,
    entity_key: 'loc_b03',
    entity_type: 'location',
    due_date: null,
    scheduled_time: null,
    status: 'pending',
    priority: 'medium',
    skill_level: 'beginner',
    stress_level: 'none',
    estimated_duration_minutes: null,
    actual_duration_minutes: null,
    requires_photo: false,
    photo_refs: [],
    timer_duration_seconds: null,
    timer_label: null,
    completion_notes: null,
    difficulty_rating: null,
    quality_rating: null,
    tags: [],
    checklist: [],
    assigned_to_user_key: null,
    recurrence_rule: null,
    recurrence_end_date: null,
    parent_recurring_task_key: null,
    trigger_phase: null,
    trigger_phase_override: null,
    reopened_at: null,
    reopened_from_status: null,
    started_at: null,
    completed_at: null,
    activity_key: null,
    template_key: null,
    workflow_execution_key: null,
    watering_event_key: null,
    created_at: null,
    updated_at: null,
    suggested: false,
    suggestion_reason: null,
    ...overrides,
  };
}

/** A request body as the server saw it. */
export interface Seen {
  url: string;
  body: unknown;
}

/**
 * The backend of a bed with a mutable pending queue: completing, skipping or reopening a task moves
 * it out of or back into the queue, so a reload shows what the server would show.
 */
export function useCareBackend(initial: CareTask[], plants: { plant_key: string; instance_id: string }[] = []) {
  const queue = new Map(initial.map((task) => [task.key, task]));
  const done = new Map<string, CareTask>();
  const seen: Seen[] = [];
  const record = async (request: Request) => {
    const text = await request.text();
    const body: unknown = text ? JSON.parse(text) : null;
    seen.push({ url: new URL(request.url).pathname.replace(/^\/api\/v1\/t\/[^/]+/, ''), body });
    return body;
  };

  server.use(
    http.get(`${BASE}/tasks/queue`, () => HttpResponse.json([...queue.values()])),
    http.get(`${BASE}/locations/:key/plantings`, () =>
      HttpResponse.json(plants.map((plant) => ({ state: 'active', species_key: 'sp', ...plant }))),
    ),
    http.post(`${BASE}/tasks/:key/complete`, async ({ request, params }) => {
      await record(request);
      const task = queue.get(String(params.key));
      if (!task) return HttpResponse.json({ detail: 'not found' }, { status: 404 });
      queue.delete(task.key);
      done.set(task.key, task);
      return HttpResponse.json({ ...task, status: 'completed' });
    }),
    http.post(`${BASE}/tasks/:key/skip`, async ({ request, params }) => {
      await record(request);
      const task = queue.get(String(params.key));
      if (task) {
        queue.delete(task.key);
        done.set(task.key, task);
      }
      return HttpResponse.json({ ...task, status: 'skipped' });
    }),
    http.post(`${BASE}/tasks/:key/reopen`, async ({ request, params }) => {
      await record(request);
      const task = done.get(String(params.key));
      if (task) {
        done.delete(task.key);
        queue.set(task.key, task);
      }
      return HttpResponse.json({ ...task, status: 'pending' });
    }),
    http.post(`${BASE}/tasks/batch/status`, async ({ request }) => {
      const body = (await record(request)) as { task_keys: string[] };
      for (const key of body.task_keys) {
        const task = queue.get(key);
        if (task) {
          queue.delete(key);
          done.set(key, task);
        }
      }
      return HttpResponse.json({ succeeded: body.task_keys, failed: [] });
    }),
    http.post(`${BASE}/tasks`, async ({ request }) => {
      const body = (await record(request)) as Partial<CareTask> & { for_each_plant?: boolean };
      if (body.for_each_plant) {
        const created = plants.map((plant, index) =>
          careTask(`plant_task_${index}`, {
            name: body.name ?? '',
            category: body.category ?? 'maintenance',
            entity_type: 'plant_instance',
            entity_key: plant.plant_key,
          }),
        );
        for (const task of created) queue.set(task.key, task);
        return HttpResponse.json(created, { status: 201 });
      }
      const created = careTask(`new_${queue.size + 1}`, { name: body.name ?? '', category: body.category ?? 'maintenance' });
      queue.set(created.key, created);
      return HttpResponse.json(created, { status: 201 });
    }),
    http.post(`${BASE}/care-events`, async ({ request }) => {
      await record(request);
      return HttpResponse.json({ key: 'ce_1', category: 'mulching' }, { status: 201 });
    }),
    http.post(`${BASE}/care-events/:key/void`, async ({ request }) => {
      await record(request);
      return HttpResponse.json({ key: 'ce_1' });
    }),
    http.get('/api/v1/t/:tenant/fertilizers', () => HttpResponse.json([])),
  );
  return { seen, queue, done };
}
