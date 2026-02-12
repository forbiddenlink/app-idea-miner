import { expect, test } from '@playwright/test';

const runRealApi = process.env.E2E_REAL_API === '1';
const apiBaseUrl = process.env.E2E_API_BASE_URL ?? 'http://127.0.0.1:8000';
const apiKey = process.env.E2E_API_KEY ?? 'dev-api-key';

function asObject(value: unknown): Record<string, unknown> {
  expect(value).not.toBeNull();
  expect(typeof value).toBe('object');
  return value as Record<string, unknown>;
}

test.describe('Real API contract checks', () => {
  test.skip(!runRealApi, 'Set E2E_REAL_API=1 to run real backend API contract checks.');

  test('clusters endpoint returns expected shape', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/clusters`, {
      headers: { 'X-API-Key': apiKey },
      params: {
        limit: 3,
        offset: 0,
        sort_by: 'size',
        order: 'desc',
      },
    });

    expect(response.status()).toBe(200);
    const payload = asObject(await response.json());

    expect(Array.isArray(payload.clusters)).toBe(true);
    const pagination = asObject(payload.pagination);
    expect(typeof pagination.total).toBe('number');
    expect(typeof pagination.limit).toBe('number');
    expect(typeof pagination.offset).toBe('number');
    expect(typeof pagination.has_more).toBe('boolean');

    const clusters = payload.clusters as unknown[];
    if (clusters.length > 0) {
      const first = asObject(clusters[0]);
      expect(typeof first.id).toBe('string');
      expect(typeof first.label).toBe('string');
      expect(Array.isArray(first.keywords)).toBe(true);
      expect(typeof first.idea_count).toBe('number');
      expect(typeof first.quality_score).toBe('number');
      expect(typeof first.trend_score).toBe('number');
    }
  });

  test('ideas endpoint returns expected shape and supports q/sort params', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/ideas`, {
      headers: { 'X-API-Key': apiKey },
      params: {
        limit: 5,
        offset: 0,
        q: 'app',
        sort_by: 'quality',
        order: 'desc',
      },
    });

    expect(response.status()).toBe(200);
    const payload = asObject(await response.json());

    expect(Array.isArray(payload.ideas)).toBe(true);
    const pagination = asObject(payload.pagination);
    expect(typeof pagination.total).toBe('number');
    expect(typeof pagination.limit).toBe('number');
    expect(typeof pagination.offset).toBe('number');
    expect(typeof pagination.has_more).toBe('boolean');

    const ideas = payload.ideas as unknown[];
    if (ideas.length > 0) {
      const first = asObject(ideas[0]);
      expect(typeof first.id).toBe('string');
      expect(typeof first.problem_statement).toBe('string');
      expect(typeof first.sentiment).toBe('string');
      expect(typeof first.sentiment_score).toBe('number');
      expect(typeof first.quality_score).toBe('number');

      if (first.raw_post !== null && first.raw_post !== undefined) {
        const rawPost = asObject(first.raw_post);
        expect(typeof rawPost.url).toBe('string');
        expect(typeof rawPost.title).toBe('string');
      }
    }
  });

  test('ideas endpoint validates invalid sort_by input', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/ideas`, {
      headers: { 'X-API-Key': apiKey },
      params: {
        sort_by: 'invalid-field',
      },
    });

    expect(response.status()).toBe(422);
  });
});
