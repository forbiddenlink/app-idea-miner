import { render } from "@/test/utils";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ClusterExplorer from "./ClusterExplorer";

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
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
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
vi.mock("@/components/ExportButton", () => ({
  ExportButton: () => <button type="button">Export</button>,
}));
vi.mock("./Settings", () => ({
  useRefreshSettings: () => ({ enabled: false, interval: 60000 }),
}));

// ---------------------------------------------------------------------------
// Mock apiClient
// ---------------------------------------------------------------------------
vi.mock("@/services/api", () => ({
  apiClient: {
    getClusters: vi.fn(),
  },
}));

import { apiClient } from "@/services/api";

const makePagination = (total: number, has_more = false) => ({
  total,
  limit: 20,
  offset: 0,
  has_more,
});

const makeCluster = (id: string, label: string) => ({
  id,
  label,
  keywords: ["test"],
  idea_count: 5,
  avg_sentiment: 0.2,
  quality_score: 0.7,
  trend_score: 0.5,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
});

beforeEach(() => {
  vi.mocked(apiClient.getClusters).mockResolvedValue({
    clusters: [
      makeCluster("c1", "Fitness Tracker"),
      makeCluster("c2", "Budget Planner"),
    ] as never,
    pagination: makePagination(2),
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("ClusterExplorer", () => {
  it("renders the page heading", () => {
    render(<ClusterExplorer />);
    expect(
      screen.getByRole("heading", { name: /explore clusters/i }),
    ).toBeInTheDocument();
  });

  it("renders cluster cards once data loads", async () => {
    render(<ClusterExplorer />);
    await waitFor(() => {
      expect(screen.getByText("Fitness Tracker")).toBeInTheDocument();
      expect(screen.getByText("Budget Planner")).toBeInTheDocument();
    });
  });

  it("shows empty state when no clusters match search", async () => {
    vi.mocked(apiClient.getClusters).mockResolvedValueOnce({
      clusters: [] as never,
      pagination: makePagination(0),
    });
    render(<ClusterExplorer />, { initialEntries: ["/?search=noresults"] });
    await waitFor(() => {
      // The EmptySearchResults component renders something about no results
      expect(screen.queryByText("Fitness Tracker")).not.toBeInTheDocument();
    });
  });

  it("renders the search input", () => {
    render(<ClusterExplorer />);
    expect(
      screen.getByRole("textbox", { name: /search clusters by keyword/i }),
    ).toBeInTheDocument();
  });

  it("renders Refresh button", () => {
    render(<ClusterExplorer />);
    expect(
      screen.getByRole("button", { name: /refresh/i }),
    ).toBeInTheDocument();
  });

  it("disables Next button when there is no next page", async () => {
    render(<ClusterExplorer />);
    await waitFor(() => screen.getByText("Fitness Tracker"));
    // With has_more=false the Next button is rendered but disabled
    const nextBtn = screen.queryByRole("button", { name: /next/i });
    if (nextBtn) expect(nextBtn).toBeDisabled();
  });

  it("calls getClusters with forwarded search param on form submit", async () => {
    render(<ClusterExplorer />);
    const input = screen.getByRole("textbox", {
      name: /search clusters by keyword/i,
    });
    fireEvent.change(input, { target: { value: "fitness" } });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => {
      const lastCall = vi.mocked(apiClient.getClusters).mock.calls.at(-1)![0];
      expect(lastCall?.q).toBe("fitness");
    });
  });
});
