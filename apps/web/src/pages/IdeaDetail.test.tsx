import { render } from "@/test/utils";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import IdeaDetail from "./IdeaDetail";

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------
// Override useParams so the component thinks it's at /ideas/idea-1
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useParams: () => ({ id: "idea-1" }),
  };
});

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
vi.mock("@/components/IdeaCard", () => ({
  IdeaCard: ({ idea }: { idea: { problem_statement: string } }) => (
    <div data-testid="idea-card">{idea.problem_statement}</div>
  ),
  IdeaCardSkeleton: () => <div data-testid="idea-skeleton" />,
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
vi.mock("@/hooks/useFavorites", () => ({
  useFavorites: () => ({
    isFavorite: () => false,
    toggleFavorite: vi.fn(),
    isMutating: false,
  }),
}));
vi.mock("./Settings", () => ({
  useRefreshSettings: () => ({ enabled: false, interval: 60000 }),
}));

// ---------------------------------------------------------------------------
// Mock apiClient
// ---------------------------------------------------------------------------
vi.mock("@/services/api", () => ({
  apiClient: {
    getIdeaById: vi.fn(),
    getIdeas: vi.fn(),
  },
}));

import { apiClient } from "@/services/api";

const mockIdea = {
  id: "idea-1",
  raw_post_id: "p1",
  problem_statement: "I wish there was an app for tracking water intake",
  context: "Staying hydrated is hard without reminders.",
  sentiment: "positive" as const,
  sentiment_score: 0.8,
  quality_score: 0.9,
  domain: "Health",
  extracted_at: "2025-01-01T00:00:00Z",
  cluster_id: "c1",
  cluster: { id: "c1", label: "Wellness Cluster" },
  source_url: "https://reddit.com/r/wellness/123",
};

beforeEach(() => {
  vi.mocked(apiClient.getIdeaById).mockResolvedValue(mockIdea as never);
  vi.mocked(apiClient.getIdeas).mockResolvedValue({
    ideas: [],
    pagination: { total: 0, limit: 8, offset: 0, has_more: false },
  } as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("IdeaDetail", () => {
  it("shows a loading state initially", () => {
    // getIdeaById never resolves to keep loading state visible
    vi.mocked(apiClient.getIdeaById).mockReturnValue(new Promise(() => {}));
    const { container } = render(<IdeaDetail />);
    // During loading the component renders skeleton pulses (no back link yet)
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("renders the problem statement after data loads", async () => {
    render(<IdeaDetail />);
    await waitFor(() => {
      expect(screen.getByText(/tracking water intake/i)).toBeInTheDocument();
    });
  });

  it("renders the idea context", async () => {
    render(<IdeaDetail />);
    await waitFor(() => {
      expect(screen.getByText(/staying hydrated is hard/i)).toBeInTheDocument();
    });
  });

  it("renders a link to the parent cluster", async () => {
    render(<IdeaDetail />);
    await waitFor(() => {
      const link = screen.getByRole("link", { name: /open cluster/i });
      expect(link).toHaveAttribute("href", "/clusters/c1");
    });
  });

  it("renders a link to the source URL", async () => {
    render(<IdeaDetail />);
    await waitFor(() => {
      const link = screen.getByRole("link", { name: /view source/i });
      expect(link).toHaveAttribute("href", mockIdea.source_url);
    });
  });

  it("renders Save Idea button", async () => {
    render(<IdeaDetail />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /save idea/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows error state when API call fails", async () => {
    vi.mocked(apiClient.getIdeaById).mockRejectedValue(new Error("Not found"));
    render(<IdeaDetail />);
    await waitFor(() => {
      expect(screen.getByText(/not found|failed|error/i)).toBeInTheDocument();
    });
  });
});
