import { describe, expect, it } from 'vitest';
import { createRequestLimiter, RequestDroppedError } from '@/api/requestLimiter';

/** A task whose promise the test settles by hand, recording that it started. */
function deferredTask<T>(started: string[], name: string) {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  const task = () => {
    started.push(name);
    return promise;
  };
  return { task, resolve, reject };
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

describe('createRequestLimiter (#3032)', () => {
  it('runs at most `limit` tasks at once and starts the next as one settles', async () => {
    const limiter = createRequestLimiter(2);
    const started: string[] = [];
    const a = deferredTask<string>(started, 'a');
    const b = deferredTask<string>(started, 'b');
    const c = deferredTask<string>(started, 'c');

    const results = [limiter.run(a.task), limiter.run(b.task), limiter.run(c.task)];
    await flush();
    expect(started).toEqual(['a', 'b']);

    a.resolve('A');
    await flush();
    expect(started).toEqual(['a', 'b', 'c']);

    b.resolve('B');
    c.resolve('C');
    await expect(Promise.all(results)).resolves.toEqual(['A', 'B', 'C']);
  });

  it('frees the slot of a task that rejects', async () => {
    const limiter = createRequestLimiter(1);
    const started: string[] = [];
    const a = deferredTask<string>(started, 'a');
    const b = deferredTask<string>(started, 'b');

    const first = limiter.run(a.task);
    const second = limiter.run(b.task);
    a.reject(new Error('boom'));
    await expect(first).rejects.toThrow('boom');
    await flush();
    expect(started).toEqual(['a', 'b']);
    b.resolve('B');
    await expect(second).resolves.toBe('B');
  });

  it('drops queued tasks when their signal aborts, without ever starting them', async () => {
    const limiter = createRequestLimiter(1);
    const started: string[] = [];
    const controller = new AbortController();
    const a = deferredTask<string>(started, 'a');
    const b = deferredTask<string>(started, 'b');
    const c = deferredTask<string>(started, 'c');

    const running = limiter.run(a.task, controller.signal);
    const queued = limiter.run(b.task, controller.signal);
    const other = limiter.run(c.task);
    controller.abort();

    await expect(queued).rejects.toBeInstanceOf(RequestDroppedError);
    // The task already running finishes; the dropped one never starts, the next caller's does.
    a.resolve('A');
    await expect(running).resolves.toBe('A');
    await flush();
    expect(started).toEqual(['a', 'c']);
    c.resolve('C');
    await expect(other).resolves.toBe('C');
  });

  it('rejects a task whose signal is already aborted', async () => {
    const limiter = createRequestLimiter(1);
    const started: string[] = [];
    const controller = new AbortController();
    controller.abort();
    const a = deferredTask<string>(started, 'a');

    await expect(limiter.run(a.task, controller.signal)).rejects.toBeInstanceOf(RequestDroppedError);
    expect(started).toEqual([]);
  });

  it('refuses a limit below one', () => {
    expect(() => createRequestLimiter(0)).toThrow(RangeError);
  });
});
