import { render } from "@/test/utils";
import type { Cluster } from "@/types";
import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ClusterCard from "./ClusterCard";

// Stub framer-motion
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, className, ...rest }: React.ComponentProps<"div">) => (
      <div className={className} {...rest}>
        {children}
      </div>
    ),
  },
}));

// Stub EnhancedTooltip — we test it in isolation; here we just need its children
vi.mock("./EnhancedTooltip", () => ({
  EnhancedTooltip: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

// Stub ContextMenu — just render children
vi.mock("./ContextMenu", () => ({
  ContextMenu: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  createClusterContextMenu: () => [],
}));

// Stub useFavorites
const mockToggleFavorite = vi.fn();
const mockIsFavorite = vi.fn(() => false);

vi.mock("@/hooks/useFavorites", () => ({
  useFavorites: () => ({
    isFavorite: mockIsFavorite,
    toggleFavorite: mockToggleFavorite,
  }),
}));

const mockCluster: Cluster = {
  id: "abc-123",
  label: "Fitness Tracking Apps",
  keywords: ["fitness", "tracking", "workout"],
  idea_count: 12,
  avg_sentiment: 0.4,
  quality_score: 0.75,
  trend_score: 0.5,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
};

describe("ClusterCard", () => {
  beforeEach(() => {
    mockIsFavorite.mockReturnValue(false);
    mockToggleFavorite.mockReset();
  });

  it("renders the cluster label", () => {
    render(<ClusterCard cluster={mockCluster} />);
    expect(screen.getByText("Fitness Tracking Apps")).toBeInTheDocument();
  });

  it("links to the cluster detail page", () => {
    render(<ClusterCard cluster={mockCluster} />);
    const link = screen.getByRole("link", {
      name: /view cluster: fitness tracking apps/i,
    });
    expect(link).toHaveAttribute("href", "/clusters/abc-123");
  });

  it("renders the favorite button as not-pressed when not favorited", () => {
    render(<ClusterCard cluster={mockCluster} />);
    const btn = screen.getByRole("button", {
      name: /add fitness tracking apps to favorites/i,
    });
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });

  it("calls toggleFavorite when the favorite button is clicked", () => {
    render(<ClusterCard cluster={mockCluster} />);
    const btn = screen.getByRole("button", { name: /favorites/i });
    fireEvent.click(btn);
    expect(mockToggleFavorite).toHaveBeenCalledWith("abc-123");
  });

  it("renders aria-pressed=true when cluster is favorited", () => {
    mockIsFavorite.mockReturnValue(true);
    render(<ClusterCard cluster={mockCluster} />);
    const btn = screen.getByRole("button", {
      name: /remove fitness tracking apps from favorites/i,
    });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("renders the idea count", () => {
    render(<ClusterCard cluster={mockCluster} />);
    expect(screen.getByText(/12/)).toBeInTheDocument();
  });
});
