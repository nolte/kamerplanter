import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import * as care from '@/api/endpoints/careReminders';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('careReminders endpoints', () => {
  it('getDashboard gets with default north hemisphere', async () => {
    client.get.mockResolvedValue({ data: [] });
    await care.getDashboard();
    expect(client.get).toHaveBeenCalledWith('/care-reminders/dashboard', {
      params: { hemisphere: 'north' },
    });
  });

  it('getDashboard passes south hemisphere', async () => {
    client.get.mockResolvedValue({ data: [] });
    await care.getDashboard('south');
    expect(client.get).toHaveBeenCalledWith('/care-reminders/dashboard', {
      params: { hemisphere: 'south' },
    });
  });

  it('getOrCreateProfile gets without optional params', async () => {
    client.get.mockResolvedValue({ data: { key: 'cp1' } });
    await care.getOrCreateProfile('pl1');
    expect(client.get).toHaveBeenCalledWith('/care-reminders/plants/pl1/profile', {
      params: {},
    });
  });

  it('getOrCreateProfile adds species and family params', async () => {
    client.get.mockResolvedValue({ data: { key: 'cp1' } });
    await care.getOrCreateProfile('pl1', 'Monstera', 'Araceae');
    expect(client.get).toHaveBeenCalledWith('/care-reminders/plants/pl1/profile', {
      params: { species_name: 'Monstera', botanical_family: 'Araceae' },
    });
  });

  it('updateProfile patches profile updates', async () => {
    client.patch.mockResolvedValue({ data: { key: 'cp1' } });
    const updates = { care_style: 'tropical' } as never;
    await care.updateProfile('pl1', updates);
    expect(client.patch).toHaveBeenCalledWith('/care-reminders/plants/pl1/profile', updates);
  });

  it('confirmReminder posts reminder type with undefined optionals', async () => {
    client.post.mockResolvedValue({ data: { key: 'c1' } });
    await care.confirmReminder('pl1', 'watering' as never);
    expect(client.post).toHaveBeenCalledWith('/care-reminders/plants/pl1/confirm', {
      reminder_type: 'watering',
      notes: undefined,
      volume_liters: undefined,
      fertilizers_used: undefined,
      measured_ec: undefined,
      measured_ph: undefined,
    });
  });

  it('confirmReminder maps all option fields into payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'c1' } });
    await care.confirmReminder('pl1', 'feeding' as never, {
      notes: 'done',
      volume_liters: 2,
      fertilizers_used: [{ fertilizer_key: 'f1', ml_applied: 5 }],
      measured_ec: 1.2,
      measured_ph: 6,
    });
    expect(client.post).toHaveBeenCalledWith('/care-reminders/plants/pl1/confirm', {
      reminder_type: 'feeding',
      notes: 'done',
      volume_liters: 2,
      fertilizers_used: [{ fertilizer_key: 'f1', ml_applied: 5 }],
      measured_ec: 1.2,
      measured_ph: 6,
    });
  });

  it('snoozeReminder posts with default snooze_days', async () => {
    client.post.mockResolvedValue({ data: { key: 'c1' } });
    await care.snoozeReminder('pl1', 'watering' as never);
    expect(client.post).toHaveBeenCalledWith('/care-reminders/plants/pl1/snooze', {
      reminder_type: 'watering',
      snooze_days: 1,
    });
  });

  it('snoozeReminder passes custom snooze_days', async () => {
    client.post.mockResolvedValue({ data: { key: 'c1' } });
    await care.snoozeReminder('pl1', 'watering' as never, 3);
    expect(client.post).toHaveBeenCalledWith('/care-reminders/plants/pl1/snooze', {
      reminder_type: 'watering',
      snooze_days: 3,
    });
  });

  it('getHistory gets without reminder_type filter', async () => {
    client.get.mockResolvedValue({ data: [] });
    await care.getHistory('pl1');
    expect(client.get).toHaveBeenCalledWith('/care-reminders/plants/pl1/history', {
      params: {},
    });
  });

  it('getHistory adds reminder_type param when provided', async () => {
    client.get.mockResolvedValue({ data: [] });
    await care.getHistory('pl1', 'watering' as never);
    expect(client.get).toHaveBeenCalledWith('/care-reminders/plants/pl1/history', {
      params: { reminder_type: 'watering' },
    });
  });

  it('resetProfile posts to reset-profile', async () => {
    client.post.mockResolvedValue({ data: { key: 'cp1' } });
    await care.resetProfile('pl1');
    expect(client.post).toHaveBeenCalledWith('/care-reminders/plants/pl1/reset-profile');
  });
});
