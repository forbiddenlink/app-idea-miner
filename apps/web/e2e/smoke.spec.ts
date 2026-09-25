/**
 * Smoke tests — fast sanity checks for every page.
 * These use mocked API responses so they run without a live backend.
 */
import { expect, test, type Page } from "@playwright/test";

async function mockAllApis(page: Page) {
  // Clusters list
  await page.route("**/api/v1/clusters**", async (route) => {
    await route.fulfill({
      json: { clusters: [], total: 0, limit: 20, offset: 0 },
    });
  });

  // Ideas list
  await page.route("**/api/v1/ideas**", async (route) => {
    await route.fulfill({
      json: { ideas: [], total: 0, limit: 20, offset: 0 },
    });
  });

  // Analytics summary. This shape mirrors AnalyticsSummaryResponse in
  // apps/api/app/schemas/analytics.py: overview and trending are nested
  // objects, not flat keys. A flat mock crashes Dashboard's StatsGrid on
  // `summary.overview.total_clusters` and the page falls into the
  // ErrorBoundary.
  await page.route("**/api/v1/analytics**", async (route) => {
    await route.fulfill({
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
    });
  });

  // Bookmarks
  await page.route("**/api/v1/bookmarks**", async (route) => {
    await route.fulfill({ json: { bookmarks: [], total: 0 } });
  });

  // Opportunities
  await page.route("**/api/v1/opportunities**", async (route) => {
    await route.fulfill({
      json: { opportunities: [], total: 0, limit: 20, offset: 0 },
    });
  });
}

/**
 * A route that throws after mount still renders its nav for a moment, so
 * `expect(nav).toBeVisible()` passes on a page that has already crashed. Assert
 * the ErrorBoundary fallback is absent as well.
 */
async function expectRendered(page: Page) {
  await expect(page.locator("nav")).toBeVisible();
  await page.waitForLoadState("networkidle");
  await expect(page.getByText("Something went wrong")).toHaveCount(0);
}

test.describe("Smoke tests — all pages render", () => {
  test("Dashboard loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/");
    await expect(page).not.toHaveTitle("Error");
    await expectRendered(page);
  });

  test("Cluster Explorer loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/clusters");
    await expectRendered(page);
  });

  test("Ideas page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/ideas");
    await expectRendered(page);
  });

  test("Opportunities page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/opportunities");
    await expectRendered(page);
  });

  test("Saved page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/saved");
    await expectRendered(page);
  });

  test("Settings page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/settings");
    await expectRendered(page);
  });

  test("404 page renders for unknown route", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/this-page-does-not-exist");
    await expect(
      page.getByRole("heading", { name: /page not found/i }),
    ).toBeVisible();
  });
});

test.describe("Smoke tests — navigation works", () => {
  test.skip("Can navigate between pages via nav links", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/");
    await page.waitForSelector('a[href="/ideas"]', { timeout: 15000 });
    await page.evaluate(() => {
      const ideasLink = document.querySelector(
        'a[href="/ideas"]',
      ) as HTMLAnchorElement | null;
      if (!ideasLink) throw new Error("Ideas link not found");
      ideasLink.click();
    });

    await expect(page).toHaveURL(/\/ideas/);
  });
});
