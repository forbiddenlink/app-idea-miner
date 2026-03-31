import { render } from "@/test/utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "./Dashboard";

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, className, ...rest }: React.ComponentProps<"div">) => (
      <div className={className} {...rest}>
        {children}
      </div>
    ),
  },
  useReducedMotion: () => false,
}));

vi.mock("@/components/EnhancedTooltip", () => ({
  EnhancedTooltip: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  SimpleTooltip: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));
vi.mock("@/components/ContextMenu", () => ({
  ContextMenu: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  createClusterContextMenu: () => [],
}));
vi.mock("@/hooks/useFavorites", () => ({
  useFavorites: () => ({ isFavorite: () => false, toggleFavorite: vi.fn() }),
}));
vi.mock("@/components/DataFreshness", () => ({
  default: () => <span data-testid="data-freshness" />,
}));
vi.mock("@/contexts/ToastContext", () => ({
  useGlobalToast: () => ({ success: vi.fn(), error: vi.fn() }),
  ToastProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

// Stub Settings so localStorage reads don't blow up
vi.mock("./Settings", () => ({
  useRefreshSettings: () => ({ enabled: false, interval: 60000 }),
}));

// ---------------------------------------------------------------------------
// Mock apiClient
// ---------------------------------------------------------------------------
const mockSummary = {
  overview: {
    total_clusters: 42,
    total_ideas: 1234,
    total_posts: 5678,
    avg_sentiment: 0.35,
  },
  trending: { new_clusters_this_week: 3, new_ideas_today: 12 },
  sentiment_distribution: { positive: 600, neutral: 500, negative: 134 },
  top_domains: [],
  recent_activity: [],
};

const mockClusters = [
  {
    id: "c1",
    label: "Fitness Tracker",
    keywords: ["fitness", "health"],
    idea_count: 10,
    avg_sentiment: 0.4,
    quality_score: 0.8,
    trend_score: 0.9,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-02T00:00:00Z",
  },
];

vi.mock("@/services/api", () => ({
  apiClient: {
    getAnalyticsSummary: vi.fn(),
    getClusters: vi.fn(),
    getOpportunities: vi.fn(),
    getIdeas: vi.fn(),
    triggerIngestion: vi.fn(),
    triggerClustering: vi.fn(),
  },
}));

import { apiClient } from "@/services/api";

beforeEach(() => {
  vi.mocked(apiClient.getAnalyticsSummary).mockResolvedValue(
    mockSummary as never,
  );
  vi.mocked(apiClient.getClusters).mockResolvedValue({
    clusters: mockClusters as never,
    pagination: { total: 1, limit: 6, offset: 0, has_more: false },
  });
  vi.mocked(apiClient.getOpportunities).mockResolvedValue({
    opportunities: [],
    pagination: { total: 0, limit: 3, offset: 0, has_more: false },
  });
  vi.mocked(apiClient.getIdeas).mockResolvedValue({
    ideas: [],
    pagination: { total: 0, limit: 5, offset: 0, has_more: false },
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Dashboard", () => {
  it("renders the page heading", async () => {
    render(<Dashboard />);
    expect(
      screen.getByRole("heading", { name: /dashboard/i }),
    ).toBeInTheDocument();
  });

  it("renders stat values once analytics data loads", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument(); // total_clusters
      expect(screen.getByText("1234")).toBeInTheDocument(); // total_ideas
    });
  });

  it("renders trending cluster cards", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("Fitness Tracker")).toBeInTheDocument();
    });
  });

  it("shows Run Ingestion and Re-cluster quick action buttons", async () => {
    render(<Dashboard />);
    expect(
      await screen.findByRole("button", { name: /run ingestion/i }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /re-cluster/i }),
    ).toBeInTheDocument();
  });

  it("shows View Opportunities link", async () => {
    render(<Dashboard />);
    const links = await screen.findAllByRole("link", {
      name: /view opportunities/i,
    });
    expect(links.length).toBeGreaterThan(0);
  });

  it("renders Refresh button", () => {
    render(<Dashboard />);
    expect(
      screen.getByRole("button", { name: /refresh/i }),
    ).toBeInTheDocument();
  });
});
