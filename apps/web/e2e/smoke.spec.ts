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

  // Analytics
  await page.route("**/api/v1/analytics**", async (route) => {
    await route.fulfill({
      json: {
        total_posts: 0,
        total_ideas: 0,
        total_clusters: 0,
        avg_quality_score: 0,
        avg_sentiment_score: 0,
        sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
        top_domains: [],
        ideas_per_day: [],
        quality_distribution: [],
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

test.describe("Smoke tests — all pages render", () => {
  test("Dashboard loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/");
    await expect(page).not.toHaveTitle("Error");
    // Navbar is present
    await expect(page.locator("nav")).toBeVisible();
  });

  test("Cluster Explorer loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/clusters");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("Ideas page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/ideas");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("Opportunities page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/opportunities");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("Saved page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/saved");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("Settings page loads", async ({ page }) => {
    await mockAllApis(page);
    await page.goto("/settings");
    await expect(page.locator("nav")).toBeVisible();
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
