import { render } from "@/test/utils";
import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Saved from "./Saved";

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------
vi.mock("@/components/ClusterCard", () => ({
  default: ({ cluster }: { cluster: { label: string } }) => (
    <div data-testid="cluster-card">{cluster.label}</div>
  ),
}));
vi.mock("@/components/IdeaCard", () => ({
  IdeaCard: ({ idea }: { idea: { problem_statement: string } }) => (
    <div data-testid="idea-card">{idea.problem_statement}</div>
  ),
}));

// ---------------------------------------------------------------------------
// useFavorites mock — overridden per-test via mockReturnValue
// ---------------------------------------------------------------------------
vi.mock("@/hooks/useFavorites", () => ({
  useFavorites: vi.fn(),
}));

import { useFavorites } from "@/hooks/useFavorites";

const mockUseFavorites = vi.mocked(useFavorites);

const emptyFavorites = {
  favorites: [],
  getFavorites: () => [],
  clearFavorites: vi.fn(),
  isLoading: false,
  error: null,
  itemCounts: { cluster: 0, idea: 0, total: 0 },
  isMutating: false,
  isFavorite: () => false,
  toggleFavorite: vi.fn(),
  addFavorite: vi.fn(),
  removeFavorite: vi.fn(),
};

beforeEach(() => {
  mockUseFavorites.mockReturnValue(emptyFavorites as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Saved", () => {
  it("shows loading skeletons while data is loading", () => {
    mockUseFavorites.mockReturnValue({
      ...emptyFavorites,
      isLoading: true,
    } as never);
    const { container } = render(<Saved />);
    expect(screen.getByText("Saved")).toBeInTheDocument();
    // Skeleton pulses exist
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("shows error message when load fails", () => {
    mockUseFavorites.mockReturnValue({
      ...emptyFavorites,
      error: new Error("network"),
    } as never);
    render(<Saved />);
    expect(screen.getByText(/failed to load saved items/i)).toBeInTheDocument();
  });

  it("shows empty state heading when no favorites", () => {
    render(<Saved />);
    expect(screen.getByText(/no saved items yet/i)).toBeInTheDocument();
  });

  it("shows Browse Clusters link in empty state", () => {
    render(<Saved />);
    const link = screen.getByRole("link", { name: /browse clusters/i });
    expect(link).toHaveAttribute("href", "/clusters");
  });

  it("shows Browse Ideas link in empty state", () => {
    render(<Saved />);
    const link = screen.getByRole("link", { name: /browse ideas/i });
    expect(link).toHaveAttribute("href", "/ideas");
  });

  it("renders cluster cards when cluster favorites exist", () => {
    const clusterBookmark = {
      id: "b1",
      item_id: "c1",
      item_type: "cluster" as const,
      created_at: "2025-01-01T00:00:00Z",
      cluster: {
        id: "c1",
        label: "Fitness App",
        description: "Health tracking",
        keywords: ["fitness"],
        idea_count: 5,
        avg_sentiment: 0.4,
        quality_score: 0.8,
        trend_score: 0.7,
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
      },
    };
    mockUseFavorites.mockReturnValue({
      ...emptyFavorites,
      favorites: [clusterBookmark],
      getFavorites: (type: string) =>
        type === "cluster" ? [clusterBookmark] : [],
      itemCounts: { cluster: 1, idea: 0, total: 1 },
    } as never);

    render(<Saved />);
    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.getByTestId("cluster-card")).toBeInTheDocument();
    expect(screen.getByText("Fitness App")).toBeInTheDocument();
  });

  it("renders idea cards when idea favorites exist", () => {
    const ideaBookmark = {
      id: "b2",
      item_id: "i1",
      item_type: "idea" as const,
      created_at: "2025-01-01T00:00:00Z",
      idea: {
        id: "i1",
        problem_statement: "I wish there was an app for tracking water intake",
        context: "",
        sentiment: "positive" as const,
        sentiment_score: 0.8,
        quality_score: 0.9,
        raw_post: { id: "p1", url: "https://example.com" },
        extracted_at: "2025-01-01T00:00:00Z",
      },
    };
    mockUseFavorites.mockReturnValue({
      ...emptyFavorites,
      favorites: [ideaBookmark],
      getFavorites: (type: string) => (type === "idea" ? [ideaBookmark] : []),
      itemCounts: { cluster: 0, idea: 1, total: 1 },
    } as never);

    render(<Saved />);
    expect(screen.getByTestId("idea-card")).toBeInTheDocument();
    expect(screen.getByText(/tracking water intake/i)).toBeInTheDocument();
  });
});
