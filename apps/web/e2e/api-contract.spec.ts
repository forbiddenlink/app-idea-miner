import { expect, test, type APIRequestContext } from "@playwright/test";

const runRealApi = process.env.E2E_REAL_API === "1";
const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";
const apiKey = process.env.E2E_API_KEY ?? "dev-api-key";

function asObject(value: unknown): Record<string, unknown> {
  expect(value).not.toBeNull();
  expect(typeof value).toBe("object");
  return value as Record<string, unknown>;
}

async function registerContractUser(
  request: APIRequestContext,
): Promise<string> {
  const email = `contract-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`;
  const response = await request.post(`${apiBaseUrl}/api/v1/auth/register`, {
    headers: { "X-API-Key": apiKey },
    data: {
      email,
      password: "ContractPass123!",
    },
  });

  expect(response.status()).toBe(201);
  const payload = asObject(await response.json());
  expect(typeof payload.access_token).toBe("string");
  return payload.access_token as string;
}

test.describe("Real API contract checks", () => {
  test.skip(
    !runRealApi,
    "Set E2E_REAL_API=1 to run real backend API contract checks.",
  );

  test("clusters endpoint returns expected shape", async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/clusters`, {
      headers: { "X-API-Key": apiKey },
      params: {
        limit: 3,
        offset: 0,
        sort_by: "size",
        order: "desc",
      },
    });

    expect(response.status()).toBe(200);
    const payload = asObject(await response.json());

    expect(Array.isArray(payload.clusters)).toBe(true);
    const pagination = asObject(payload.pagination);
    expect(typeof pagination.total).toBe("number");
    expect(typeof pagination.limit).toBe("number");
    expect(typeof pagination.offset).toBe("number");
    expect(typeof pagination.has_more).toBe("boolean");

    const clusters = payload.clusters as unknown[];
    if (clusters.length > 0) {
      const first = asObject(clusters[0]);
      expect(typeof first.id).toBe("string");
      expect(typeof first.label).toBe("string");
      expect(Array.isArray(first.keywords)).toBe(true);
      expect(typeof first.idea_count).toBe("number");
      expect(typeof first.quality_score).toBe("number");
      expect(typeof first.trend_score).toBe("number");
    }
  });

  test("ideas endpoint returns expected shape and supports q/sort params", async ({
    request,
  }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/ideas`, {
      headers: { "X-API-Key": apiKey },
      params: {
        limit: 5,
        offset: 0,
        q: "app",
        sort_by: "quality",
        order: "desc",
      },
    });

    expect(response.status()).toBe(200);
    const payload = asObject(await response.json());

    expect(Array.isArray(payload.ideas)).toBe(true);
    const pagination = asObject(payload.pagination);
    expect(typeof pagination.total).toBe("number");
    expect(typeof pagination.limit).toBe("number");
    expect(typeof pagination.offset).toBe("number");
    expect(typeof pagination.has_more).toBe("boolean");

    const ideas = payload.ideas as unknown[];
    if (ideas.length > 0) {
      const first = asObject(ideas[0]);
      expect(typeof first.id).toBe("string");
      expect(typeof first.problem_statement).toBe("string");
      expect(typeof first.sentiment).toBe("string");
      expect(typeof first.sentiment_score).toBe("number");
      expect(typeof first.quality_score).toBe("number");

      if (first.raw_post !== null && first.raw_post !== undefined) {
        const rawPost = asObject(first.raw_post);
        expect(typeof rawPost.url).toBe("string");
        expect(typeof rawPost.title).toBe("string");
      }
    }
  });

  test("ideas endpoint validates invalid sort_by input", async ({
    request,
  }) => {
    const response = await request.get(`${apiBaseUrl}/api/v1/ideas`, {
      headers: { "X-API-Key": apiKey },
      params: {
        sort_by: "invalid-field",
      },
    });

    expect(response.status()).toBe(422);
  });

  test("bookmarks list and clear endpoints return expected shape", async ({
    request,
  }) => {
    const accessToken = await registerContractUser(request);

    const authHeaders = {
      "X-API-Key": apiKey,
      Authorization: `Bearer ${accessToken}`,
    };

    const listResponse = await request.get(`${apiBaseUrl}/api/v1/bookmarks`, {
      headers: authHeaders,
      params: { limit: 20, offset: 0 },
    });

    expect(listResponse.status()).toBe(200);
    const listPayload = asObject(await listResponse.json());
    expect(Array.isArray(listPayload.bookmarks)).toBe(true);
    const pagination = asObject(listPayload.pagination);
    expect(typeof pagination.total).toBe("number");
    expect(typeof pagination.limit).toBe("number");
    expect(typeof pagination.offset).toBe("number");
    expect(typeof pagination.has_more).toBe("boolean");

    const clearResponse = await request.delete(
      `${apiBaseUrl}/api/v1/bookmarks`,
      {
        headers: authHeaders,
      },
    );

    expect(clearResponse.status()).toBe(200);
    const clearPayload = asObject(await clearResponse.json());
    expect(typeof clearPayload.success).toBe("boolean");
    expect(typeof clearPayload.deleted).toBe("number");
  });
});
