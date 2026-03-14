import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  Sparkles,
  TrendingUp,
  Target,
  Heart,
  Award,
  Globe,
  ChevronDown,
  ArrowUpRight,
  Filter,
} from "lucide-react"

import { apiClient } from "@/services/api"
import { Opportunity, OpportunityScoreBreakdown } from "@/types"
import DataFreshness from "@/components/DataFreshness"
import { useRefreshSettings } from "./Settings"
import { Button } from "@/components/ui/button"

function getGradeColor(grade: string): string {
  switch (grade) {
    case "A":
      return "text-grade-a"
    case "B":
      return "text-grade-b"
    case "C":
      return "text-grade-c"
    case "D":
      return "text-grade-d"
    case "F":
      return "text-grade-f"
    default:
      return "text-muted-foreground"
  }
}

function getGradeBg(grade: string): string {
  switch (grade) {
    case "A":
      return "bg-grade-a/10 border-grade-a/20"
    case "B":
      return "bg-grade-b/10 border-grade-b/20"
    case "C":
      return "bg-grade-c/10 border-grade-c/20"
    case "D":
      return "bg-grade-d/10 border-grade-d/20"
    case "F":
      return "bg-grade-f/10 border-grade-f/20"
    default:
      return "bg-muted/10 border-muted/20"
  }
}

function ScoreBar({
  label,
  icon: Icon,
  data,
}: Readonly<{
  label: string
  icon: React.ElementType
  data: OpportunityScoreBreakdown
}>) {
  const pct = (data.score / data.max) * 100
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <Icon className="h-3.5 w-3.5" />
          {label}
        </span>
        <span className="font-medium">
          {data.score}/{data.max}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted/50">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, delay: 0.1 }}
        />
      </div>
      <p className="text-xs text-muted-foreground">{data.description}</p>
    </div>
  )
}

function OpportunityCard({ opportunity }: Readonly<{ opportunity: Opportunity }>) {
  const { opportunity_score: score } = opportunity
  const [expanded, setExpanded] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden border rounded-xl border-border bg-card"
    >
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Link
                to={`/clusters/${opportunity.cluster_id}`}
                className="text-lg font-semibold truncate transition-colors hover:text-primary"
              >
                {opportunity.cluster_label}
              </Link>
              <ArrowUpRight className="flex-shrink-0 w-4 h-4 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">{score.verdict}</p>
          </div>

          {/* Score Badge */}
          <div
            className={`flex flex-col items-center rounded-lg border px-4 py-2 ${getGradeBg(score.grade)}`}
          >
            <span className={`text-2xl font-bold ${getGradeColor(score.grade)}`}>
              {score.total}
            </span>
            <span
              className={`text-xs font-semibold ${getGradeColor(score.grade)}`}
            >
              Grade {score.grade}
            </span>
          </div>
        </div>

        {/* Keywords */}
        <div className="flex flex-wrap gap-1.5 mt-3">
          {opportunity.keywords.slice(0, 5).map((keyword) => (
            <span
              key={keyword}
              className="inline-flex items-center rounded-md bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground"
            >
              {keyword}
            </span>
          ))}
          {opportunity.idea_count > 0 && (
            <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs text-primary font-medium">
              {opportunity.idea_count} ideas
            </span>
          )}
        </div>
      </div>

      {/* Expandable Breakdown */}
      <div className="border-t border-border">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full px-6 py-3 text-sm transition-colors text-muted-foreground hover:text-foreground"
        >
          <span>Score Breakdown</span>
          <ChevronDown
            className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </button>

        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-6 pb-6 space-y-4"
          >
            <ScoreBar label="Demand" icon={Target} data={score.breakdown.demand} />
            <ScoreBar
              label="Quality"
              icon={Award}
              data={score.breakdown.quality}
            />
            <ScoreBar
              label="Sentiment"
              icon={Heart}
              data={score.breakdown.sentiment}
            />
            <ScoreBar
              label="Trend"
              icon={TrendingUp}
              data={score.breakdown.trend}
            />
            <ScoreBar
              label="Diversity"
              icon={Globe}
              data={score.breakdown.diversity}
            />
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

export default function Opportunities() {
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings()
  const [sortBy, setSortBy] = useState<"score" | "demand" | "trend">("score")
  const [minScore, setMinScore] = useState(0)

  const { data, isLoading, error, dataUpdatedAt, isRefetching } = useQuery({
    queryKey: ["opportunities", { sort_by: sortBy, min_score: minScore }],
    queryFn: () =>
      apiClient.getOpportunities({
        sort_by: sortBy,
        min_score: minScore,
        limit: 50,
      }),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  const opportunities = data?.opportunities || []

  // Summary stats
  const gradeDistribution = opportunities.reduce(
    (acc, opp) => {
      const grade = opp.opportunity_score.grade
      acc[grade] = (acc[grade] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 sm:py-8 space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-6 h-6 text-primary" />
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Opportunity Scores
            </h2>
          </div>
          <p className="text-muted-foreground">
            Market validation scores for each opportunity cluster, ranked by
            potential.
          </p>
        </div>
        {dataUpdatedAt > 0 && (
          <DataFreshness
            dataUpdatedAt={dataUpdatedAt}
            isRefetching={isRefetching}
          />
        )}
      </div>

      {/* Grade Summary */}
      {!isLoading && opportunities.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {(["A", "B", "C", "D", "F"] as const).map((grade) => (
            <div
              key={grade}
              className={`rounded-lg border p-4 text-center ${getGradeBg(grade)}`}
            >
              <div className={`text-2xl font-bold ${getGradeColor(grade)}`}>
                {gradeDistribution[grade] || 0}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Grade {grade}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Filter className="w-4 h-4" />
          Sort by:
        </div>
        {(
          [
            { value: "score", label: "Score" },
            { value: "demand", label: "Demand" },
            { value: "trend", label: "Trend" },
          ] as const
        ).map((option) => (
          <Button
            key={option.value}
            variant={sortBy === option.value ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy(option.value)}
          >
            {option.label}
          </Button>
        ))}

        <div className="flex items-center gap-2 ml-auto text-sm">
          <label htmlFor="min-score" className="text-muted-foreground">
            Min score:
          </label>
          <input
            id="min-score"
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-16 px-2 py-1 text-sm border rounded-md border-border bg-background"
          />
        </div>
      </div>

      {/* Opportunity Cards */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2">
          {["skel-1", "skel-2", "skel-3", "skel-4", "skel-5", "skel-6"].map((id) => (
            <div
              key={id}
              className="h-48 rounded-xl bg-muted/50 animate-pulse"
            />
          ))}
        </div>
      )}

      {!isLoading && error && (
        <div className="py-12 text-center">
          <p className="text-destructive">
            Failed to load opportunities. Please try again.
          </p>
        </div>
      )}

      {!isLoading && !error && opportunities.length === 0 && (
        <div className="py-12 text-center">
          <Sparkles className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
          <h3 className="text-lg font-semibold">No opportunities found</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {minScore > 0
              ? `No clusters scored above ${minScore}. Try lowering the minimum.`
              : "Run clustering to generate opportunity scores."}
          </p>
        </div>
      )}

      {!isLoading && !error && opportunities.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {opportunities.map((opp) => (
            <OpportunityCard key={opp.cluster_id} opportunity={opp} />
          ))}
        </div>
      )}
    </div>
  )
}
