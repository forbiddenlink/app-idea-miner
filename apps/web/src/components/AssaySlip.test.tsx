import { render } from "@/test/utils";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Opportunity } from "@/types";
import AssaySlip from "./AssaySlip";

const opportunity: Opportunity = {
  cluster_id: "c1",
  cluster_label: "Reading tracker",
  keywords: ["reading", "books"],
  idea_count: 7,
  opportunity_score: {
    total: 61,
    grade: "B",
    verdict: "Promising opportunity — worth further validation",
    breakdown: {
      demand: { score: 30, max: 30, description: "7 ideas detected" },
      sentiment: { score: 12, max: 20, description: "Avg sentiment: 0.20" },
      quality: { score: 10, max: 25, description: "Quality score: 0.40" },
      trend: { score: 5, max: 15, description: "Trend score: 0.33" },
      diversity: { score: 4, max: 10, description: "2 unique domain(s)" },
    },
  },
};

describe("AssaySlip", () => {
  it("renders the score breakdown on the 100-point scale", () => {
    const { container } = render(
      <AssaySlip opportunity={opportunity} isLoading={false} />,
    );
    expect(screen.getByText("Reading tracker")).toBeInTheDocument();
    expect(screen.getByLabelText("Grade B")).toBeInTheDocument();
    expect(screen.getByLabelText("Demand 30 of 30")).toBeInTheDocument();
    expect(container.querySelectorAll(".assay-tick")).toHaveLength(100);
    expect(container.querySelectorAll('.assay-tick[data-on="true"]')).toHaveLength(
      61,
    );
  });

  it("shows the verdict without an em dash", () => {
    render(<AssaySlip opportunity={opportunity} isLoading={false} />);
    expect(
      screen.getByText("Promising opportunity: worth further validation"),
    ).toBeInTheDocument();
  });

  it("explains the empty state", () => {
    render(<AssaySlip opportunity={undefined} isLoading={false} />);
    expect(screen.getByText("Nothing scored yet.")).toBeInTheDocument();
  });
});
