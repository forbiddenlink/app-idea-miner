import { expect, test, type Page } from '@playwright/test';

type IdeaFixture = {
  id: string;
  problem_statement: string;
  context: string;
  domain: string;
  cluster_id: string;
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
    cluster_id: `cluster-${Math.ceil(id / 5)}`,
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
  await page.route('**/api/v1/ideas**', async (route) => {
    const requestUrl = new URL(route.request().url());
    const pathname = requestUrl.pathname;

    if (pathname.startsWith('/api/v1/ideas/')) {
      const ideaId = pathname.split('/').pop() ?? '';
      const idea = ideasSeed.find((item) => item.id === ideaId);

      if (!idea) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Idea not found' }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...idea,
          emotions: {},
          features_mentioned: [],
          cluster: {
            id: idea.cluster_id,
            label: `Cluster ${idea.cluster_id.replace('cluster-', '')}`,
          },
          raw_post: {
            id: `post-${idea.id}`,
            url: `https://example.com/${idea.id}`,
            title: `Post for ${idea.id}`,
            source: 'test',
            published_at: idea.extracted_at,
          },
        }),
      });
      return;
    }
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
    const clusterId = requestUrl.searchParams.get('cluster_id') ?? '';
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
    if (clusterId) {
      filtered = filtered.filter((idea) => idea.cluster_id === clusterId);
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
          cluster: {
            id: idea.cluster_id,
            label: `Cluster ${idea.cluster_id.replace('cluster-', '')}`,
          },
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

async function mockBookmarksApi(page: Page) {
  const bookmarks = new Map<string, { item_type: 'cluster' | 'idea'; item_id: string; created_at: string }>();

  await page.route('**/api/v1/bookmarks**', async (route) => {
    const request = route.request();
    const requestUrl = new URL(request.url());
    const scopeKey = requestUrl.searchParams.get('scope_key') ?? 'default';
    const pathnameParts = requestUrl.pathname.split('/').filter(Boolean);
    const isDeleteSingle =
      request.method() === 'DELETE' &&
      pathnameParts.length >= 5 &&
      pathnameParts[0] === 'api' &&
      pathnameParts[1] === 'v1' &&
      pathnameParts[2] === 'bookmarks';
    const itemTypeFromPath = isDeleteSingle ? pathnameParts[3] : undefined;
    const itemIdFromPath = isDeleteSingle ? pathnameParts[4] : undefined;

    if (request.method() === 'GET') {
      const list = Array.from(bookmarks.entries())
        .filter(([key]) => key.startsWith(`${scopeKey}:`))
        .map(([, item]) => ({
          item_type: item.item_type,
          item_id: item.item_id,
          scope_key: scopeKey,
          created_at: item.created_at,
          cluster: null,
          idea: null,
        }));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          bookmarks: list,
          pagination: {
            total: list.length,
            limit: Number(requestUrl.searchParams.get('limit') ?? '20'),
            offset: Number(requestUrl.searchParams.get('offset') ?? '0'),
            has_more: false,
          },
        }),
      });
      return;
    }

    if (request.method() === 'POST') {
      const body = JSON.parse(request.postData() ?? '{}') as {
        scope_key?: string;
        item_type?: 'cluster' | 'idea';
        item_id?: string;
      };

      const itemType = body.item_type ?? 'cluster';
      const itemId = body.item_id ?? '';
      const itemScope = body.scope_key ?? scopeKey;
      if (itemId) {
        bookmarks.set(`${itemScope}:${itemType}:${itemId}`, {
          item_type: itemType,
          item_id: itemId,
          created_at: new Date().toISOString(),
        });
      }

      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Bookmark saved' }),
      });
      return;
    }

    if (request.method() === 'DELETE' && itemTypeFromPath && itemIdFromPath) {
      bookmarks.delete(`${scopeKey}:${itemTypeFromPath}:${itemIdFromPath}`);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Bookmark removed' }),
      });
      return;
    }

    if (request.method() === 'DELETE') {
      for (const key of Array.from(bookmarks.keys())) {
        if (key.startsWith(`${scopeKey}:`)) {
          bookmarks.delete(key);
        }
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, deleted: 0 }),
      });
      return;
    }

    await route.continue();
  });
}

test.beforeEach(async ({ page }) => {
  await mockIdeasApi(page);
  await mockBookmarksApi(page);
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
  await page.getByRole('button', { name: 'Close mobile menu' }).evaluate((element) => {
    (element as HTMLButtonElement).click();
  });
  await expect(page.locator('#mobile-navigation-menu')).toHaveCount(0);
});

test('idea detail route loads and links related ideas', async ({ page }) => {
  await page.goto('/ideas/idea-5');

  await expect(page.getByRole('heading', { name: 'Budget tracker for teams' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open Cluster' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Related Ideas' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'View idea details' }).first()).toBeVisible();
});
