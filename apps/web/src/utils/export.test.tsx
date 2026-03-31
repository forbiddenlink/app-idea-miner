import type { Cluster, DomainStats, Idea } from "@/types";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  exportAsCSV,
  exportAsJSON,
  exportClusterEvidence,
  exportDomainBreakdown,
} from "./export";

// ---------------------------------------------------------------------------
// DOM / browser API stubs
// ---------------------------------------------------------------------------
const mockClick = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();
const mockRevokeObjectURL = vi.fn();

beforeEach(() => {
  mockClick.mockClear();
  mockAppendChild.mockClear();
  mockRemoveChild.mockClear();
  mockRevokeObjectURL.mockClear();

  // createObjectURL isn't in jsdom
  vi.stubGlobal("URL", {
    createObjectURL: vi.fn(() => "blob:mock-url"),
    revokeObjectURL: mockRevokeObjectURL,
  });

  const mockAnchor = {
    href: "",
    download: "",
    click: mockClick,
    remove: vi.fn(),
  } as unknown as HTMLAnchorElement;

  vi.spyOn(document, "createElement").mockReturnValue(mockAnchor);
  vi.spyOn(document.body, "appendChild").mockImplementation(mockAppendChild);
  vi.spyOn(document.body, "removeChild").mockImplementation(mockRemoveChild);
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// exportAsJSON
// ---------------------------------------------------------------------------
describe("exportAsJSON", () => {
  it("triggers a download by clicking an anchor element", () => {
    exportAsJSON({ foo: "bar" }, "test-file");
    expect(mockClick).toHaveBeenCalledOnce();
  });

  it("sets the download filename with .json extension", () => {
    exportAsJSON({}, "my-export");
    const anchor = (document.createElement as ReturnType<typeof vi.fn>).mock
      .results[0].value as HTMLAnchorElement;
    expect(anchor.download).toBe("my-export.json");
  });

  it("revokes the object URL after download", () => {
    exportAsJSON({}, "cleanup-test");
    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
  });
});

// ---------------------------------------------------------------------------
// exportAsCSV — tests the CSV serialisation logic via the triggered download
// ---------------------------------------------------------------------------
describe("exportAsCSV", () => {
  it("triggers a download", () => {
    exportAsCSV([{ name: "Alice", score: 10 }], "results");
    expect(mockClick).toHaveBeenCalledOnce();
  });

  it("sets the download filename with .csv extension", () => {
    exportAsCSV([{ a: 1 }], "sheet");
    const anchor = (document.createElement as ReturnType<typeof vi.fn>).mock
      .results[0].value as HTMLAnchorElement;
    expect(anchor.download).toBe("sheet.csv");
  });

  it("does nothing (warns) when given an empty array", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    exportAsCSV([], "empty");
    expect(mockClick).not.toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalledWith("No data to export");
    warnSpy.mockRestore();
  });
});

// ---------------------------------------------------------------------------
// exportClusterEvidence
// ---------------------------------------------------------------------------
const mockCluster: Cluster = {
  id: "c1",
  label: "Fitness Apps",
  keywords: ["fitness", "health"],
  idea_count: 2,
  avg_sentiment: 0.5,
  quality_score: 0.8,
  trend_score: 0.6,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
};

const mockIdea: Idea = {
  id: "i1",
  raw_post_id: "p1",
  problem_statement: "Need a better workout tracker",
  sentiment: "positive",
  sentiment_score: 0.7,
  quality_score: 0.9,
  extracted_at: "2025-03-01T00:00:00Z",
};

describe("exportClusterEvidence", () => {
  it("triggers a CSV download by default", () => {
    exportClusterEvidence(mockCluster, [mockIdea]);
    expect(mockClick).toHaveBeenCalledOnce();
  });

  it("triggers a JSON download when format is json", () => {
    exportClusterEvidence(mockCluster, [mockIdea], "json");
    expect(mockClick).toHaveBeenCalledOnce();
  });

  it("uses the cluster label in the filename", () => {
    exportClusterEvidence(mockCluster, [mockIdea], "json");
    const anchor = (document.createElement as ReturnType<typeof vi.fn>).mock
      .results[0].value as HTMLAnchorElement;
    expect(anchor.download).toMatch(/fitness-apps/);
  });
});

// ---------------------------------------------------------------------------
// exportDomainBreakdown
// ---------------------------------------------------------------------------
const mockDomains: DomainStats[] = [
  { domain: "health", idea_count: 10, avg_sentiment: 0.5, percentage: 50 },
  { domain: "finance", idea_count: 10, avg_sentiment: 0.3, percentage: 50 },
];

describe("exportDomainBreakdown", () => {
  it("triggers a CSV download by default", () => {
    exportDomainBreakdown(mockDomains);
    expect(mockClick).toHaveBeenCalledOnce();
  });

  it("triggers a JSON download when format is json", () => {
    exportDomainBreakdown(mockDomains, "json");
    expect(mockClick).toHaveBeenCalledOnce();
  });
});
