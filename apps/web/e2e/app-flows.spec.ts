import { expect, test, type Page } from '@playwright/test';

type IdeaFixture = {
  id: string;
  problem_statement: string;
  context: string;
  domain: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_score: number;
  quality_score: number;
  extracted_at: string;
};

const ideasSeed: IdeaFixture[] = Array.from({ length: 25 }, (_, idx) => {
  const id = idx + 1;
  const sentiment: IdeaFixture['sentiment'] =
    id % 3 === 0 ? 'positive' : id % 3 === 1 ? 'neutral' : 'negative';

  return {
    id: `idea-${id}`,
    problem_statement: `General idea ${id}`,
    context: `Context for general idea ${id}`,
    domain: id % 2 === 0 ? 'finance' : 'social',
    sentiment,
    sentiment_score: sentiment === 'positive' ? 0.8 : sentiment === 'negative' ? -0.5 : 0.1,
    quality_score: Number((1 - idx * 0.02).toFixed(2)),
    extracted_at: new Date(Date.UTC(2026, 0, id)).toISOString(),
  };
});

ideasSeed[4] = {
  ...ideasSeed[4],
  problem_statement: 'Budget tracker for teams',
  context: 'Finance teams still reconcile spending manually',
  domain: 'finance',
  sentiment: 'positive',
  sentiment_score: 0.9,
  quality_score: 0.97,
};

async function mockIdeasApi(page: Page) {
  await page.route('**/api/v1/ideas*', async (route) => {
    const requestUrl = new URL(route.request().url());
    const pathname = requestUrl.pathname;

    if (pathname !== '/api/v1/ideas') {
      await route.continue();
      return;
    }

    const limit = Number(requestUrl.searchParams.get('limit') ?? '20');
    const offset = Number(requestUrl.searchParams.get('offset') ?? '0');
    const sortBy = requestUrl.searchParams.get('sort_by') ?? 'quality';
    const order = requestUrl.searchParams.get('order') ?? 'desc';
    const q = (requestUrl.searchParams.get('q') ?? '').toLowerCase();
    const sentiment = requestUrl.searchParams.get('sentiment') ?? '';
    const domain = requestUrl.searchParams.get('domain') ?? '';
    const minQualityRaw = requestUrl.searchParams.get('min_quality');
    const minQuality = minQualityRaw ? Number(minQualityRaw) : undefined;

    let filtered = [...ideasSeed];

    if (q) {
      filtered = filtered.filter(
        (idea) =>
          idea.problem_statement.toLowerCase().includes(q) ||
          idea.context.toLowerCase().includes(q)
      );
    }

    if (sentiment) {
      filtered = filtered.filter((idea) => idea.sentiment === sentiment);
    }

    if (domain) {
      filtered = filtered.filter((idea) => idea.domain === domain);
    }

    if (typeof minQuality === 'number' && !Number.isNaN(minQuality)) {
      filtered = filtered.filter((idea) => idea.quality_score >= minQuality);
    }

    filtered.sort((a, b) => {
      const multiplier = order === 'asc' ? 1 : -1;
      if (sortBy === 'date') {
        return (
          (new Date(a.extracted_at).getTime() - new Date(b.extracted_at).getTime()) * multiplier
        );
      }
      if (sortBy === 'sentiment') {
        return (a.sentiment_score - b.sentiment_score) * multiplier;
      }
      return (a.quality_score - b.quality_score) * multiplier;
    });

    const paged = filtered.slice(offset, offset + limit);

    if (offset === 20) {
      await new Promise((resolve) => setTimeout(resolve, 600));
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ideas: paged.map((idea) => ({
          ...idea,
          emotions: {},
          features_mentioned: [],
          raw_post: {
            id: `post-${idea.id}`,
            url: `https://example.com/${idea.id}`,
            title: `Post for ${idea.id}`,
            source: 'test',
            published_at: idea.extracted_at,
          },
        })),
        pagination: {
          total: filtered.length,
          limit,
          offset,
          has_more: offset + limit < filtered.length,
        },
      }),
    });
  });
}

test.beforeEach(async ({ page }) => {
  await mockIdeasApi(page);
});

test('ideas search and filters sync with URL and results', async ({ page }) => {
  await page.goto('/ideas');

  await expect(page.getByRole('heading', { name: 'Ideas Browser' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /^General idea 1$/ })).toBeVisible();

  await page.fill('#search-input', 'budget');
  await expect
    .poll(() => new URL(page.url()).searchParams.get('search'))
    .toBe('budget');

  await expect(page.getByText('Budget tracker for teams')).toBeVisible();

  await page.selectOption('#sentiment-select', 'positive');
  await expect
    .poll(() => new URL(page.url()).searchParams.get('sentiment'))
    .toBe('positive');

  await expect(page.getByText('of 1 ideas')).toBeVisible();
});

test('ideas pagination keeps previous page visible during fetch transition', async ({ page }) => {
  await page.goto('/ideas');

  await expect(page.getByRole('heading', { name: /^General idea 1$/ })).toBeVisible();

  await page.getByRole('button', { name: 'Next' }).click();

  await expect(page.getByTestId('ideas-updating-indicator')).toBeVisible();
  await expect(page.getByRole('heading', { name: /^General idea 1$/ })).toBeVisible();

  await expect(page.getByRole('heading', { name: /^General idea 21$/ })).toBeVisible();
  await expect(page).toHaveURL(/offset=20/);
});

test('mobile navigation opens and closes with escape and backdrop click', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/ideas');

  await page.getByRole('button', { name: 'Open menu' }).click();
  await expect(page.getByRole('button', { name: 'Open Command Palette' })).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(page.locator('#mobile-navigation-menu')).toHaveCount(0);

  await page.getByRole('button', { name: 'Open menu' }).click();
  await page.getByRole('button', { name: 'Close mobile menu' }).click({ force: true });
  await expect(page.locator('#mobile-navigation-menu')).toHaveCount(0);
});
