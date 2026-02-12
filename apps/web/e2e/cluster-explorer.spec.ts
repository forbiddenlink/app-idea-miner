import { expect, test, type Page } from '@playwright/test';

type ClusterFixture = {
  id: string;
  label: string;
  description: string;
  keywords: string[];
  idea_count: number;
  avg_sentiment: number;
  quality_score: number;
  trend_score: number;
  created_at: string;
  updated_at: string;
};

const clustersSeed: ClusterFixture[] = Array.from({ length: 30 }, (_, idx) => {
  const id = idx + 1;
  return {
    id: `cluster-${id}`,
    label: `General Cluster ${id}`,
    description: `Description for general cluster ${id}`,
    keywords: [`keyword-${id}`, 'automation', 'productivity'],
    idea_count: 5 + id,
    avg_sentiment: Number((0.6 - id * 0.02).toFixed(2)),
    quality_score: Number((0.95 - id * 0.01).toFixed(2)),
    trend_score: Number((0.3 + id * 0.02).toFixed(2)),
    created_at: new Date(Date.UTC(2026, 0, id)).toISOString(),
    updated_at: new Date(Date.UTC(2026, 0, id)).toISOString(),
  };
});

clustersSeed[5] = {
  ...clustersSeed[5],
  label: 'Budget Ops Cluster',
  description: 'Operations teams track monthly spend manually',
  keywords: ['budget', 'finance', 'ops'],
  idea_count: 24,
  trend_score: 0.92,
};

async function mockClustersApi(page: Page) {
  await page.route('**/api/v1/clusters*', async (route) => {
    const requestUrl = new URL(route.request().url());

    if (requestUrl.pathname !== '/api/v1/clusters') {
      await route.continue();
      return;
    }

    const sortBy = requestUrl.searchParams.get('sort_by') ?? 'size';
    const order = requestUrl.searchParams.get('order') ?? 'desc';
    const minSizeRaw = requestUrl.searchParams.get('min_size');
    const minSize = minSizeRaw ? Number(minSizeRaw) : undefined;
    const q = (requestUrl.searchParams.get('q') ?? '').toLowerCase();
    const limit = Number(requestUrl.searchParams.get('limit') ?? '20');
    const offset = Number(requestUrl.searchParams.get('offset') ?? '0');

    let filtered = [...clustersSeed];

    if (q) {
      filtered = filtered.filter(
        (cluster) =>
          cluster.label.toLowerCase().includes(q) ||
          cluster.description.toLowerCase().includes(q) ||
          cluster.keywords.some((keyword) => keyword.toLowerCase().includes(q))
      );
    }

    if (typeof minSize === 'number' && !Number.isNaN(minSize)) {
      filtered = filtered.filter((cluster) => cluster.idea_count >= minSize);
    }

    const fieldMap = {
      size: 'idea_count',
      quality: 'quality_score',
      sentiment: 'avg_sentiment',
      trend: 'trend_score',
      created_at: 'created_at',
    } as const;

    const field = fieldMap[sortBy as keyof typeof fieldMap] ?? 'idea_count';
    const multiplier = order === 'asc' ? 1 : -1;

    filtered.sort((a, b) => {
      if (field === 'created_at') {
        return (
          (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()) * multiplier
        );
      }
      return ((a[field] as number) - (b[field] as number)) * multiplier;
    });

    const paged = filtered.slice(offset, offset + limit);

    if (offset === 20) {
      await new Promise((resolve) => setTimeout(resolve, 600));
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        clusters: paged,
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
  await mockClustersApi(page);
});

test('cluster filters update URL and clear-all resets back to defaults', async ({ page }) => {
  await page.goto('/clusters');

  await expect(page.getByRole('heading', { name: 'Explore Clusters' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /^General Cluster 30$/ })).toBeVisible();

  await page.getByPlaceholder('Search clusters by keyword...').fill('budget');
  await page.getByRole('button', { name: 'Go' }).click();

  await expect
    .poll(() => new URL(page.url()).searchParams.get('search'))
    .toBe('budget');
  await expect(page.getByRole('heading', { name: 'Budget Ops Cluster' })).toBeVisible();

  await page.fill('#min-size-input', '20');
  await expect
    .poll(() => new URL(page.url()).searchParams.get('min_size'))
    .toBe('20');

  await page.selectOption('#sort-by-select', 'trend');
  await expect
    .poll(() => new URL(page.url()).searchParams.get('sort_by'))
    .toBe('trend');

  await page.getByRole('button', { name: 'Sort low to high' }).click();
  await expect
    .poll(() => new URL(page.url()).searchParams.get('order'))
    .toBe('asc');

  await expect(page.getByText('Active Filters:')).toBeVisible();
  await page.getByRole('button', { name: 'Clear All' }).click();

  await expect
    .poll(() => new URL(page.url()).search)
    .toBe('');
  await expect(page.getByText('Active Filters:')).toHaveCount(0);
});

test('cluster pagination keeps previous page rendered while next page fetches', async ({ page }) => {
  await page.goto('/clusters');

  await expect(page.getByRole('heading', { name: /^General Cluster 30$/ })).toBeVisible();

  await page.getByRole('button', { name: 'Next' }).click();

  await expect(page.getByText('Updating clusters...')).toBeVisible();
  await expect(page.getByRole('heading', { name: /^General Cluster 30$/ })).toBeVisible();

  await expect(page.getByRole('heading', { name: /^General Cluster 21$/ })).toBeVisible();
  await expect(page).toHaveURL(/offset=20/);
});
