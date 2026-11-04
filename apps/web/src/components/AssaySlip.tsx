import { Link } from "react-router-dom";

import type { Opportunity, OpportunityScore } from "@/types";
import { formatVerdict } from "@/utils/verdict";

const AXES: ReadonlyArray<{
  key: keyof OpportunityScore["breakdown"];
  label: string;
}> = [
  { key: "demand", label: "Demand" },
  { key: "sentiment", label: "Sentiment" },
  { key: "quality", label: "Quality" },
  { key: "trend", label: "Trend" },
  { key: "diversity", label: "Diversity" },
];

const GRADE_TEXT: Record<string, string> = {
  A: "text-grade-a",
  B: "text-grade-b-fg",
  C: "text-grade-c",
  D: "text-grade-d",
  F: "text-grade-f",
};

/**
 * The product's own output: the top-scored cluster, with the five signals that
 * add up to its 0-100 opportunity score. Each signal is drawn as `max` ticks, so
 * the five rows together are the 100-point scale itself.
 */
export default function AssaySlip({
  opportunity,
  isLoading,
}: Readonly<{ opportunity: Opportunity | undefined; isLoading: boolean }>) {
  if (!opportunity) {
    return (
      <section
        aria-label="Top scored opportunity"
        className="card relative min-h-[17rem] overflow-hidden p-6 sm:p-8"
      >
        <p className="section-kicker">Top scored opportunity</p>
        {isLoading ? (
          <div className="mt-6 space-y-4" aria-hidden="true">
            <div className="h-10 w-2/3 animate-pulse rounded bg-muted/60" />
            <div className="h-4 w-1/3 animate-pulse rounded bg-muted/60" />
            <div className="h-24 animate-pulse rounded bg-muted/40" />
          </div>
        ) : (
          <div className="mt-6 max-w-xl">
            <p className="font-display text-xl sm:text-2xl">
              Nothing scored yet.
            </p>
            <p className="mt-2 text-muted-foreground">
              Each cluster is scored 0 to 100 on demand, sentiment, quality,
              trend and diversity. Run ingestion, then re-cluster, to see the
              first one here.
            </p>
          </div>
        )}
      </section>
    );
  }

  const { opportunity_score: score } = opportunity;
  let tickIndex = 0;

  return (
    <section
      aria-label="Top scored opportunity"
      className="card relative overflow-hidden"
    >
      <div className="grid lg:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_minmax(0,24rem)]">
        <div className="flex items-end justify-between gap-4 border-b border-dashed border-border p-6 sm:p-8 lg:flex-col lg:items-start lg:justify-between lg:border-b-0 lg:border-r">
          <p className="section-kicker">Top scored opportunity</p>
          <div>
            <p
              className={`font-display text-7xl font-bold leading-none sm:text-8xl ${GRADE_TEXT[score.grade] ?? "text-foreground"}`}
              aria-label={`Grade ${score.grade}`}
            >
              {score.grade}
            </p>
            <p className="mt-3 font-mono text-sm text-muted-foreground">
              <span className="text-foreground">{score.total}</span> / 100
            </p>
          </div>
        </div>

        <div className="flex flex-col justify-between gap-6 p-6 sm:p-8">
          <div>
            <h2 className="font-display text-2xl leading-tight sm:text-3xl">
              <Link
                to={`/clusters/${opportunity.cluster_id}`}
                className="focus-ring rounded-sm hover:text-primary"
              >
                {opportunity.cluster_label}
              </Link>
            </h2>
            <p className="mt-3 text-muted-foreground">{formatVerdict(score.verdict)}</p>
          </div>
          <ul className="flex flex-wrap gap-2" aria-label="Keywords">
            {opportunity.keywords.slice(0, 5).map((kw) => (
              <li
                key={kw}
                className="rounded border border-border px-2 py-0.5 font-mono text-xs text-muted-foreground"
              >
                {kw}
              </li>
            ))}
          </ul>
        </div>

        <dl className="space-y-4 border-t border-dashed border-border p-6 sm:p-8 lg:border-l lg:border-t-0">
          {AXES.map(({ key, label }) => {
            const axis = score.breakdown[key];
            const startIndex = tickIndex;
            tickIndex += axis.max;
            return (
              <div key={key}>
                <div className="flex items-baseline justify-between gap-3">
                  <dt className="section-kicker">{label}</dt>
                  <dd className="font-mono text-xs text-foreground">
                    {axis.score}
                    <span className="text-muted-foreground"> / {axis.max}</span>
                  </dd>
                </div>
                <div
                  className="mt-1.5 flex gap-[2px]"
                  role="img"
                  aria-label={`${label} ${axis.score} of ${axis.max}`}
                >
                  {Array.from({ length: axis.max }, (_, i) => (
                    <span
                      key={i}
                      className="assay-tick"
                      data-on={i < axis.score}
                      style={{ ["--i" as string]: startIndex + i }}
                    />
                  ))}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {axis.description}
                </p>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}
