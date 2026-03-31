import { render } from "@/test/utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Ideas from "./Ideas";

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
    aside: ({
      children,
      className,
      ...rest
    }: React.ComponentProps<"aside">) => (
      <aside className={className} {...rest}>
        {children}
      </aside>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));
vi.mock("@/components/IdeaCard", () => ({
  IdeaCard: ({ idea }: { idea: { problem_statement: string } }) => (
    <div data-testid="idea-card">{idea.problem_statement}</div>
  ),
  IdeaCardSkeleton: () => (
    <div data-testid="idea-skeleton" className="animate-pulse" />
  ),
}));
vi.mock("@/components/LoadingSkeleton", () => ({
  IdeaCardSkeleton: () => (
    <div data-testid="idea-skeleton" className="animate-pulse" />
  ),
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
    getIdeas: vi.fn(),
    getAnalyticsDomains: vi.fn(),
  },
}));

import { apiClient } from "@/services/api";

const mockIdea = {
  id: "i1",
  raw_post_id: "p1",
  problem_statement: "I wish there was an app for tracking water intake",
  sentiment: "positive" as const,
  sentiment_score: 0.8,
  quality_score: 0.9,
  extracted_at: "2025-01-01T00:00:00Z",
};

const emptyResponse = {
  ideas: [],
  pagination: { total: 0, limit: 20, offset: 0, has_more: false },
};

beforeEach(() => {
  vi.mocked(apiClient.getIdeas).mockResolvedValue(emptyResponse as never);
  vi.mocked(apiClient.getAnalyticsDomains).mockResolvedValue([] as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Ideas", () => {
  it("renders the page heading", async () => {
    render(<Ideas />);
    expect(
      await screen.findByRole("heading", { name: /ideas/i }),
    ).toBeInTheDocument();
  });

  it("renders a search input", () => {
    render(<Ideas />);
    expect(screen.getByPlaceholderText(/search ideas/i)).toBeInTheDocument();
  });

  it("shows empty state when no ideas are returned", async () => {
    render(<Ideas />);
    await waitFor(() => {
      expect(screen.getByText(/no ideas found/i)).toBeInTheDocument();
    });
  });

  it("renders ideas when API returns results", async () => {
    vi.mocked(apiClient.getIdeas).mockResolvedValue({
      ideas: [mockIdea],
      pagination: { total: 1, limit: 20, offset: 0, has_more: false },
    } as never);

    render(<Ideas />);
    await waitFor(() => {
      expect(screen.getByTestId("idea-card")).toBeInTheDocument();
      expect(screen.getByText(/tracking water intake/i)).toBeInTheDocument();
    });
  });

  it("renders pagination buttons", async () => {
    // Pagination only renders when ideas are present
    vi.mocked(apiClient.getIdeas).mockResolvedValue({
      ideas: [mockIdea],
      pagination: { total: 1, limit: 20, offset: 0, has_more: false },
    } as never);
    render(<Ideas />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /previous/i }),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /next/i })).toBeInTheDocument();
    });
  });

  it("shows an error message when the API fails", async () => {
    vi.mocked(apiClient.getIdeas).mockRejectedValue(
      new Error("Service unavailable"),
    );
    render(<Ideas />);
    await waitFor(() => {
      expect(screen.getByText(/failed to load ideas/i)).toBeInTheDocument();
    });
  });
});
