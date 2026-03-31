import { render } from "@/test/utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Opportunities from "./Opportunities";

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
vi.mock("@/components/DataFreshness", () => ({
  default: () => <span data-testid="data-freshness" />,
}));
vi.mock("./Settings", () => ({
  useRefreshSettings: () => ({ enabled: false, interval: 60000 }),
}));

// ---------------------------------------------------------------------------
// Mock apiClient
// ---------------------------------------------------------------------------
vi.mock("@/services/api", () => ({
  apiClient: {
    getOpportunities: vi.fn(),
  },
}));

import { apiClient } from "@/services/api";

const mockOpportunity = {
  cluster_id: "c1",
  cluster_label: "Fitness Tracker",
  keywords: ["fitness", "health", "tracker"],
  idea_count: 12,
  opportunity_score: {
    total: 78,
    grade: "B",
    verdict: "Strong opportunity with clear demand",
    breakdown: {
      demand: { score: 20, max: 25, description: "High posting frequency" },
      quality: { score: 18, max: 25, description: "Good signal quality" },
      sentiment: { score: 15, max: 20, description: "Mostly positive" },
      trend: { score: 14, max: 20, description: "Growing interest" },
      diversity: { score: 11, max: 10, description: "Multiple sources" },
    },
  },
};

const emptyResponse = {
  opportunities: [],
  pagination: { total: 0, limit: 50, offset: 0, has_more: false },
};

beforeEach(() => {
  vi.mocked(apiClient.getOpportunities).mockResolvedValue(
    emptyResponse as never,
  );
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Opportunities", () => {
  it("renders the page heading", async () => {
    render(<Opportunities />);
    expect(
      await screen.findByRole("heading", { name: /opportunities/i }),
    ).toBeInTheDocument();
  });

  it("shows empty state when there are no opportunities", async () => {
    render(<Opportunities />);
    await waitFor(() => {
      expect(screen.getByText(/no opportunities/i)).toBeInTheDocument();
    });
  });

  it("renders an opportunity card with the cluster label", async () => {
    vi.mocked(apiClient.getOpportunities).mockResolvedValue({
      opportunities: [mockOpportunity],
      pagination: { total: 1, limit: 50, offset: 0, has_more: false },
    } as never);

    render(<Opportunities />);
    await waitFor(() => {
      expect(screen.getByText("Fitness Tracker")).toBeInTheDocument();
    });
  });

  it("links the cluster label to the cluster detail page", async () => {
    vi.mocked(apiClient.getOpportunities).mockResolvedValue({
      opportunities: [mockOpportunity],
      pagination: { total: 1, limit: 50, offset: 0, has_more: false },
    } as never);

    render(<Opportunities />);
    await waitFor(() => {
      const link = screen.getByRole("link", { name: /fitness tracker/i });
      expect(link).toHaveAttribute("href", "/clusters/c1");
    });
  });

  it("displays the grade badge", async () => {
    vi.mocked(apiClient.getOpportunities).mockResolvedValue({
      opportunities: [mockOpportunity],
      pagination: { total: 1, limit: 50, offset: 0, has_more: false },
    } as never);

    render(<Opportunities />);
    // "Grade B" appears in both the summary grid and the individual card badge
    await waitFor(() => {
      const gradeLabels = screen.getAllByText("Grade B");
      expect(gradeLabels.length).toBeGreaterThan(0);
    });
  });

  it("displays the verdict text", async () => {
    vi.mocked(apiClient.getOpportunities).mockResolvedValue({
      opportunities: [mockOpportunity],
      pagination: { total: 1, limit: 50, offset: 0, has_more: false },
    } as never);

    render(<Opportunities />);
    await waitFor(() => {
      expect(
        screen.getByText(/strong opportunity with clear demand/i),
      ).toBeInTheDocument();
    });
  });

  it("shows an error message when the API call fails", async () => {
    vi.mocked(apiClient.getOpportunities).mockRejectedValue(
      new Error("Server error"),
    );
    render(<Opportunities />);
    await waitFor(() => {
      expect(screen.getByText(/failed to load|error/i)).toBeInTheDocument();
    });
  });
});
