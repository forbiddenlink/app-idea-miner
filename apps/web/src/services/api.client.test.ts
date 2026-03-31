/**
 * Tests for ApiClient methods — verifies that each method calls the correct
 * endpoint and forwards the right params/payload. The underlying axios instance
 * is replaced by stubs using vi.hoisted so the mock is available before the
 * api.ts module is imported.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Stub the axios instance that ApiClient creates internally via axios.create()
// ---------------------------------------------------------------------------
const { mockGet, mockPost, mockDelete, mockPatch } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
  mockPatch: vi.fn(),
}));

vi.mock("axios", async (importOriginal) => {
  const actual = await importOriginal<typeof import("axios")>();
  return {
    ...actual,
    default: {
      ...actual.default,
      create: vi.fn(() => ({
        get: mockGet,
        post: mockPost,
        delete: mockDelete,
        patch: mockPatch,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      })),
    },
  };
});

// Import after the mock is in place
import { apiClient } from "./api";

const ok = (data: unknown) =>
  Promise.resolve({
    data,
    status: 200,
    statusText: "OK",
    headers: {},
    config: {},
  });

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockDelete.mockReset();
  mockPatch.mockReset();
});

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
describe("getHealth", () => {
  it("calls GET /health", async () => {
    mockGet.mockResolvedValueOnce(ok({ status: "ok" }));
    const result = await apiClient.getHealth();
    expect(mockGet).toHaveBeenCalledWith("/health");
    expect(result).toEqual({ status: "ok" });
  });
});

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------
describe("getAnalyticsSummary", () => {
  it("calls GET /api/v1/analytics/summary", async () => {
    mockGet.mockResolvedValueOnce(ok({ overview: {} }));
    await apiClient.getAnalyticsSummary();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/analytics/summary");
  });
});

describe("getAnalyticsTrends", () => {
  it("calls GET /api/v1/analytics/trends with params forwarded", async () => {
    mockGet.mockResolvedValueOnce(ok({}));
    await apiClient.getAnalyticsTrends({ metric: "ideas", days: 7 });
    expect(mockGet).toHaveBeenCalledWith("/api/v1/analytics/trends", {
      params: { metric: "ideas", days: 7 },
    });
  });
});

describe("getAnalyticsDomains", () => {
  it("calls GET /api/v1/analytics/domains and maps domain name field", async () => {
    mockGet.mockResolvedValueOnce(
      ok({
        domains: [
          {
            name: "health",
            idea_count: 10,
            avg_sentiment: 0.5,
            percentage: 40,
          },
        ],
      }),
    );
    const result = await apiClient.getAnalyticsDomains();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/analytics/domains");
    expect(result[0].domain).toBe("health");
  });
});

// ---------------------------------------------------------------------------
// Clusters
// ---------------------------------------------------------------------------
describe("getClusters", () => {
  it("calls GET /api/v1/clusters", async () => {
    mockGet.mockResolvedValueOnce(ok({ clusters: [], pagination: {} }));
    await apiClient.getClusters();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters", {
      params: undefined,
    });
  });

  it("forwards query params", async () => {
    mockGet.mockResolvedValueOnce(ok({ clusters: [], pagination: {} }));
    await apiClient.getClusters({ sort_by: "trend", limit: 5 });
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters", {
      params: { sort_by: "trend", limit: 5 },
    });
  });
});

describe("getCluster", () => {
  it("calls GET /api/v1/clusters/:id with evidence_limit=5 by default", async () => {
    mockGet.mockResolvedValueOnce(ok({ id: "abc" }));
    await apiClient.getCluster("abc");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters/abc", {
      params: { evidence_limit: 5 },
    });
  });

  it("sets evidence_limit=0 when includeEvidence is false", async () => {
    mockGet.mockResolvedValueOnce(ok({ id: "abc" }));
    await apiClient.getCluster("abc", false);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters/abc", {
      params: { evidence_limit: 0 },
    });
  });
});

describe("getSimilarClusters", () => {
  it("calls GET /api/v1/clusters/:id/similar", async () => {
    mockGet.mockResolvedValueOnce(ok({ similar_clusters: [] }));
    await apiClient.getSimilarClusters("xyz", 3);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters/xyz/similar", {
      params: { limit: 3 },
    });
  });
});

describe("getTrendingClusters", () => {
  it("calls GET /api/v1/clusters/trending/list with correct params", async () => {
    mockGet.mockResolvedValueOnce(ok({ trending: [] }));
    await apiClient.getTrendingClusters(10, 0.5);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/clusters/trending/list", {
      params: { limit: 10, min_trend_score: 0.5 },
    });
  });
});

// ---------------------------------------------------------------------------
// Ideas
// ---------------------------------------------------------------------------
describe("getIdeas", () => {
  it("calls GET /api/v1/ideas", async () => {
    mockGet.mockResolvedValueOnce(ok({ ideas: [], pagination: {} }));
    await apiClient.getIdeas();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/ideas", {
      params: undefined,
    });
  });

  it("forwards query params", async () => {
    mockGet.mockResolvedValueOnce(ok({ ideas: [] }));
    await apiClient.getIdeas({ sort_by: "date", limit: 10 });
    expect(mockGet).toHaveBeenCalledWith("/api/v1/ideas", {
      params: { sort_by: "date", limit: 10 },
    });
  });
});

describe("getIdeaById", () => {
  it("calls GET /api/v1/ideas/:id", async () => {
    mockGet.mockResolvedValueOnce(ok({ id: "i1" }));
    await apiClient.getIdeaById("i1");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/ideas/i1");
  });
});

describe("searchIdeas", () => {
  it("calls GET /api/v1/ideas/search/query with q and limit", async () => {
    mockGet.mockResolvedValueOnce(ok({ results: [] }));
    await apiClient.searchIdeas("fitness app", 15);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/ideas/search/query", {
      params: { q: "fitness app", limit: 15 },
    });
  });

  it("defaults limit to 20", async () => {
    mockGet.mockResolvedValueOnce(ok({ results: [] }));
    await apiClient.searchIdeas("test");
    const [, opts] = mockGet.mock.calls[0];
    expect(opts.params.limit).toBe(20);
  });
});

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------
describe("triggerIngestion", () => {
  it("calls POST /api/v1/jobs/ingest", async () => {
    mockPost.mockResolvedValueOnce(ok({ job_id: "j1" }));
    await apiClient.triggerIngestion();
    expect(mockPost).toHaveBeenCalledWith("/api/v1/jobs/ingest", {});
  });
});

describe("triggerClustering", () => {
  it("calls POST /api/v1/jobs/recluster with empty body by default", async () => {
    mockPost.mockResolvedValueOnce(ok({ job_id: "j2" }));
    await apiClient.triggerClustering();
    expect(mockPost).toHaveBeenCalledWith("/api/v1/jobs/recluster", {});
  });

  it("forwards params when provided", async () => {
    mockPost.mockResolvedValueOnce(ok({ job_id: "j3" }));
    await apiClient.triggerClustering({ min_cluster_size: 3 });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/jobs/recluster", {
      min_cluster_size: 3,
    });
  });
});

describe("getJobStatus", () => {
  it("calls GET /api/v1/jobs/:id", async () => {
    mockGet.mockResolvedValueOnce(ok({ job_id: "j1", status: "running" }));
    await apiClient.getJobStatus("j1");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/jobs/j1");
  });
});

// ---------------------------------------------------------------------------
// Opportunities
// ---------------------------------------------------------------------------
describe("getOpportunities", () => {
  it("calls GET /api/v1/opportunities", async () => {
    mockGet.mockResolvedValueOnce(ok({ opportunities: [] }));
    await apiClient.getOpportunities();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/opportunities", {
      params: undefined,
    });
  });
});

describe("getOpportunity", () => {
  it("calls GET /api/v1/opportunities/:clusterId", async () => {
    mockGet.mockResolvedValueOnce(ok({ cluster_id: "c1" }));
    await apiClient.getOpportunity("c1");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/opportunities/c1");
  });
});

// ---------------------------------------------------------------------------
// Bookmarks
// ---------------------------------------------------------------------------
describe("getBookmarks", () => {
  it("calls GET /api/v1/bookmarks", async () => {
    mockGet.mockResolvedValueOnce(ok({ items: [] }));
    await apiClient.getBookmarks();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/bookmarks", {
      params: undefined,
    });
  });
});

describe("addBookmark", () => {
  it("calls POST /api/v1/bookmarks with payload", async () => {
    mockPost.mockResolvedValueOnce(ok({ success: true }));
    await apiClient.addBookmark({
      item_type: "cluster",
      item_id: "c1",
    });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/bookmarks", {
      item_type: "cluster",
      item_id: "c1",
    });
  });
});

describe("removeBookmark", () => {
  it("calls DELETE /api/v1/bookmarks/:type/:id", async () => {
    mockDelete.mockResolvedValueOnce(ok({ success: true }));
    await apiClient.removeBookmark("cluster", "c1");
    expect(mockDelete).toHaveBeenCalledWith("/api/v1/bookmarks/cluster/c1");
  });
});

describe("clearBookmarks", () => {
  it("calls DELETE /api/v1/bookmarks", async () => {
    mockDelete.mockResolvedValueOnce(ok({ deleted: 3 }));
    await apiClient.clearBookmarks();
    expect(mockDelete).toHaveBeenCalledWith("/api/v1/bookmarks", {
      params: { item_type: undefined },
    });
  });
});

// ---------------------------------------------------------------------------
// Saved Searches
// ---------------------------------------------------------------------------
describe("getSavedSearches", () => {
  it("calls GET /api/v1/saved-searches", async () => {
    mockGet.mockResolvedValueOnce(ok({ saved_searches: [], pagination: {} }));
    await apiClient.getSavedSearches();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/saved-searches", {
      params: undefined,
    });
  });
});

describe("createSavedSearch", () => {
  it("calls POST /api/v1/saved-searches with payload", async () => {
    mockPost.mockResolvedValueOnce(ok({ success: true }));
    await apiClient.createSavedSearch({
      name: "Fintech trends",
      query_params: { domain: "fintech" },
      alert_enabled: true,
      alert_frequency: "weekly",
    });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/saved-searches", {
      name: "Fintech trends",
      query_params: { domain: "fintech" },
      alert_enabled: true,
      alert_frequency: "weekly",
    });
  });
});

describe("updateSavedSearch", () => {
  it("calls PATCH /api/v1/saved-searches/:id", async () => {
    mockPatch.mockResolvedValueOnce(ok({ success: true }));
    await apiClient.updateSavedSearch("s1", { name: "Updated" });
    expect(mockPatch).toHaveBeenCalledWith("/api/v1/saved-searches/s1", {
      name: "Updated",
    });
  });
});

describe("deleteSavedSearch", () => {
  it("calls DELETE /api/v1/saved-searches/:id", async () => {
    mockDelete.mockResolvedValueOnce(ok({ success: true }));
    await apiClient.deleteSavedSearch("s1");
    expect(mockDelete).toHaveBeenCalledWith("/api/v1/saved-searches/s1");
  });
});
