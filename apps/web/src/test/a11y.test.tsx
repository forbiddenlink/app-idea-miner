/**
 * Accessibility smoke tests.
 *
 * These tests verify key ARIA roles, labels, headings, and landmark regions
 * across the most-visited components without running a full browser.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Shared stubs
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
vi.mock("@/hooks/useFavorites", () => ({
  useFavorites: () => ({ isFavorite: () => false, toggleFavorite: vi.fn() }),
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
vi.mock("@/components/SearchAutocomplete", () => ({
  SearchAutocomplete: () => <input aria-label="Search" placeholder="Search…" />,
}));
vi.mock("@/components/mode-toggle", () => ({
  ModeToggle: () => (
    <button type="button" aria-label="Toggle theme">
      Mode
    </button>
  ),
}));

import ClusterCard from "@/components/ClusterCard";
import { StatCardSkeleton } from "@/components/LoadingSkeleton";
import Navbar from "@/components/Navbar";
import StatCard from "@/components/StatCard";
import type { Cluster } from "@/types";

// ---------------------------------------------------------------------------
// Navbar
// ---------------------------------------------------------------------------
describe("Navbar accessibility", () => {
  it("has a navigation landmark with aria-label", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );
    const nav = screen.getByRole("navigation", { name: /main navigation/i });
    expect(nav).toBeInTheDocument();
  });

  it("home link has accessible label", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("link", { name: /app-idea miner home/i }),
    ).toBeInTheDocument();
  });

  it("mobile menu button has accessible label", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("button", { name: /open menu|close menu/i }),
    ).toBeInTheDocument();
  });

  it("nav links point to correct hrefs", () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    );
    expect(
      screen.getAllByRole("link", { name: /dashboard/i })[0],
    ).toHaveAttribute("href", "/");
    expect(
      screen.getAllByRole("link", { name: /clusters/i })[0],
    ).toHaveAttribute("href", "/clusters");
  });
});

// ---------------------------------------------------------------------------
// StatCard
// ---------------------------------------------------------------------------
describe("StatCard accessibility", () => {
  it("renders name as readable text (not hidden)", () => {
    render(<StatCard name="Total Ideas" value="99" />);
    expect(screen.getByText("Total Ideas")).toBeVisible();
  });

  it("renders value as readable text", () => {
    render(<StatCard name="Ideas" value="42" />);
    expect(screen.getByText("42")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// LoadingSkeleton
// ---------------------------------------------------------------------------
describe("StatCardSkeleton accessibility", () => {
  it("does not render any interactive elements", () => {
    const { container } = render(<StatCardSkeleton />);
    expect(container.querySelectorAll("button, a, input")).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// ClusterCard
// ---------------------------------------------------------------------------
const mockCluster: Cluster = {
  id: "a1",
  label: "Fitness Apps",
  keywords: ["fitness", "health"],
  idea_count: 8,
  avg_sentiment: 0.5,
  quality_score: 0.8,
  trend_score: 0.6,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
};

describe("ClusterCard accessibility", () => {
  it("card link has accessible aria-label describing the cluster", () => {
    render(
      <MemoryRouter>
        <ClusterCard cluster={mockCluster} />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("link", { name: /view cluster: fitness apps/i }),
    ).toBeInTheDocument();
  });

  it("favorite button has aria-pressed attribute", () => {
    render(
      <MemoryRouter>
        <ClusterCard cluster={mockCluster} />
      </MemoryRouter>,
    );
    const btn = screen.getByRole("button", { name: /favorites/i });
    expect(btn).toHaveAttribute("aria-pressed");
  });

  it("favorite button aria-label explains the action", () => {
    render(
      <MemoryRouter>
        <ClusterCard cluster={mockCluster} />
      </MemoryRouter>,
    );
    const btn = screen.getByRole("button", {
      name: /add fitness apps to favorites/i,
    });
    expect(btn).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// DataFreshness (exported formatRelativeTime helper)
// ---------------------------------------------------------------------------
describe("formatRelativeTime", () => {
  it('returns "just now" for timestamps under 30 seconds ago', async () => {
    const { formatRelativeTime } = await import("@/components/DataFreshness");
    expect(formatRelativeTime(Date.now() - 5000)).toBe("just now");
  });

  it("returns seconds label between 30s and 60s", async () => {
    const { formatRelativeTime } = await import("@/components/DataFreshness");
    expect(formatRelativeTime(Date.now() - 45000)).toMatch(/s ago/);
  });

  it("returns minutes label for timestamps 1-60 minutes ago", async () => {
    const { formatRelativeTime } = await import("@/components/DataFreshness");
    expect(formatRelativeTime(Date.now() - 3 * 60 * 1000)).toMatch(/m ago/);
  });
});
