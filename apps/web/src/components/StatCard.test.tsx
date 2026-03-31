import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import StatCard from "./StatCard";

// framer-motion produces animations that are irrelevant to unit tests.
// Stub it out with a plain div so tests are fast and predictable.
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, className, ...rest }: React.ComponentProps<"div">) => (
      <div className={className} {...rest}>
        {children}
      </div>
    ),
  },
}));

describe("StatCard", () => {
  it("renders the name", () => {
    render(<StatCard name="Total Ideas" value="42" />);
    expect(screen.getByText("Total Ideas")).toBeInTheDocument();
  });

  it("renders the value", () => {
    render(<StatCard name="Clusters" value="128" />);
    expect(screen.getByText("128")).toBeInTheDocument();
  });

  it("renders the change text when provided", () => {
    render(<StatCard name="Posts" value="500" change="last 7 days" />);
    expect(screen.getByText(/last 7 days/)).toBeInTheDocument();
  });

  it("renders the trendValue when trend and trendValue are provided", () => {
    render(
      <StatCard name="Quality" value="0.82" trend="up" trendValue="+5%" />,
    );
    expect(screen.getByText("+5%")).toBeInTheDocument();
  });

  it("does not render trend section when neither change nor trendValue is provided", () => {
    const { container } = render(<StatCard name="Posts" value="10" />);
    // No border-t div should appear
    const trendRow = container.querySelector(".border-t");
    expect(trendRow).toBeNull();
  });

  it("applies extra className to the wrapper", () => {
    const { container } = render(
      <StatCard name="x" value="y" className="my-custom-class" />,
    );
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
