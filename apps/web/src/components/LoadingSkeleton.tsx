export const StatCardSkeleton = () => (
  <div className="animate-pulse rounded-lg border border-border bg-card p-6">
    <div className="space-y-3">
      <div className="h-4 w-24 rounded bg-muted"></div>
      <div className="h-8 w-16 rounded bg-muted"></div>
      <div className="h-3 w-20 rounded bg-muted/60"></div>
    </div>
  </div>
);

export const IdeaCardSkeleton = () => (
  <div className="animate-pulse rounded-lg border border-border bg-card p-5">
    <div className="space-y-3">
      <div className="h-5 w-full rounded bg-muted"></div>
      <div className="h-4 w-5/6 rounded bg-muted/60"></div>
      <div className="flex items-center gap-2 pt-2">
        <div className="h-4 w-20 rounded bg-muted/40"></div>
        <div className="h-4 w-16 rounded bg-muted/40"></div>
      </div>
    </div>
  </div>
);

export const DetailHeaderSkeleton = () => (
  <div className="animate-pulse space-y-6">
    {/* Title */}
    <div className="space-y-3">
      <div className="h-7 w-2/3 rounded bg-muted"></div>
      <div className="h-4 w-full rounded bg-muted/60"></div>
    </div>

    {/* Metric cards */}
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="rounded-lg border border-border bg-card p-4">
          <div className="mb-2 h-4 w-16 rounded bg-muted/60"></div>
          <div className="h-6 w-12 rounded bg-muted"></div>
        </div>
      ))}
    </div>

    {/* Keywords */}
    <div className="space-y-3">
      <div className="h-4 w-20 rounded bg-muted/60"></div>
      <div className="flex flex-wrap gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-6 w-16 rounded bg-muted/40"></div>
        ))}
      </div>
    </div>
  </div>
);
