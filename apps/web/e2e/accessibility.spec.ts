/**
 * WCAG gate — every route the smoke suite renders must also pass axe.
 *
 * axe-core ships with @axe-core/react, which main.tsx already loads in dev to
 * log violations to the console. A console warning nobody reads is not a gate,
 * so the same engine runs here and fails the build instead.
 */
import { expect, test, type Page } from "@playwright/test";
import { createRequire } from "node:module";
import fs from "node:fs";

const require_ = createRequire(import.meta.url);
// pnpm does not hoist axe-core, so resolve it through the package that owns it.
const axeSource = fs.readFileSync(
  require_.resolve("axe-core/axe.min.js", {
    paths: [require_.resolve("@axe-core/react")],
  }),
  "utf8",
);

const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

const ROUTES = [
  "/",
  "/clusters",
  "/ideas",
  "/opportunities",
  "/saved",
  "/settings",
  "/login",
];

interface AxeNode {
  target: string[];
}
interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: AxeNode[];
}

async function mockAllApis(page: Page) {
  await page.route("**/api/v1/clusters**", (route) =>
    route.fulfill({ json: { clusters: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.route("**/api/v1/ideas**", (route) =>
    route.fulfill({ json: { ideas: [], total: 0, limit: 20, offset: 0 } }),
  );
  // Mirrors AnalyticsSummaryResponse (apps/api/app/schemas/analytics.py):
  // overview and trending are nested, not flat.
  await page.route("**/api/v1/analytics**", (route) =>
    route.fulfill({
      json: {
        overview: {
          total_posts: 0,
          total_ideas: 0,
          total_clusters: 0,
          avg_cluster_size: 0,
          avg_sentiment: 0,
        },
        trending: {
          hot_clusters: 0,
          new_ideas_today: 0,
          new_clusters_this_week: 0,
        },
        sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
        top_domains: [],
        updated_at: "2026-01-01T00:00:00Z",
      },
    }),
  );
  await page.route("**/api/v1/bookmarks**", (route) =>
    route.fulfill({ json: { bookmarks: [], total: 0 } }),
  );
  await page.route("**/api/v1/opportunities**", (route) =>
    route.fulfill({
      json: { opportunities: [], total: 0, limit: 20, offset: 0 },
    }),
  );
}

for (const route of ROUTES) {
  test(`${route} has no WCAG 2.2 AA violations`, async ({ page }) => {
    await mockAllApis(page);
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    // A crashed route renders the ErrorBoundary fallback, which is a tiny tree
    // that passes axe trivially. Assert real content before trusting a pass.
    await expect(page.getByText("Something went wrong")).toHaveCount(0);
    await expect(page.locator("#root")).not.toBeEmpty();
    await page.addScriptTag({ content: axeSource });

    const violations = await page.evaluate(async (tags) => {
      const result = await (
        window as unknown as {
          axe: { run: (ctx: Document, opts: unknown) => Promise<unknown> };
        }
      ).axe.run(document, { runOnly: { type: "tag", values: tags } });
      return (result as { violations: AxeViolation[] }).violations;
    }, WCAG_TAGS);

    const report = violations
      .map(
        (v) =>
          `${v.impact} [${v.id}] ${v.help}\n` +
          v.nodes.map((n) => `    ${n.target.join(" ")}`).join("\n"),
      )
      .join("\n");

    expect(report, `${route} accessibility violations:\n${report}`).toBe("");
  });
}
