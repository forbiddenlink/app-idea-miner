import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  ChartSkeleton,
  ClusterCardSkeleton,
  IdeaCardSkeleton,
  StatCardSkeleton,
} from "./LoadingSkeleton";

describe("LoadingSkeleton", () => {
  describe("StatCardSkeleton", () => {
    it("renders without crashing", () => {
      const { container } = render(<StatCardSkeleton />);
      expect(container.firstChild).toBeTruthy();
    });

    it("has animate-pulse class", () => {
      const { container } = render(<StatCardSkeleton />);
      expect(container.firstChild).toHaveClass("animate-pulse");
    });
  });

  describe("ClusterCardSkeleton", () => {
    it("renders without crashing", () => {
      const { container } = render(<ClusterCardSkeleton />);
      expect(container.firstChild).toBeTruthy();
    });

    it("has animate-pulse class", () => {
      const { container } = render(<ClusterCardSkeleton />);
      expect(container.firstChild).toHaveClass("animate-pulse");
    });
  });

  describe("IdeaCardSkeleton", () => {
    it("renders without crashing", () => {
      const { container } = render(<IdeaCardSkeleton />);
      expect(container.firstChild).toBeTruthy();
    });

    it("has animate-pulse class", () => {
      const { container } = render(<IdeaCardSkeleton />);
      expect(container.firstChild).toHaveClass("animate-pulse");
    });
  });

  describe("ChartSkeleton", () => {
    it("renders without crashing", () => {
      const { container } = render(<ChartSkeleton />);
      expect(container.firstChild).toBeTruthy();
    });

    it("has animate-pulse class", () => {
      const { container } = render(<ChartSkeleton />);
      expect(container.firstChild).toHaveClass("animate-pulse");
    });
  });
});
