// Type definitions for API responses

export interface Cluster {
  id: string
  label: string
  description?: string
  keywords: string[]
  idea_count: number
  avg_sentiment: number
  quality_score: number
  trend_score: number
  created_at: string
  updated_at: string
  evidence?: Idea[]
  related_clusters?: RelatedCluster[]
}

export interface RelatedCluster {
  id: string
  label: string
  idea_count: number
  similarity_score?: number
}

export interface Idea {
  id: string
  raw_post_id: string
  problem_statement: string
  context?: string
  sentiment: 'positive' | 'neutral' | 'negative'
  sentiment_score: number
  emotions?: {
    frustration?: number
    hope?: number
    urgency?: number
  }
  domain?: string
  features_mentioned?: string[]
  quality_score: number
  cluster_id?: string
  cluster?: {
    id: string
    label: string
  }
  source_url?: string
  source?: string
  raw_post?: {
    id?: string
    url?: string
    title?: string
    source?: string
    published_at?: string
  }
  extracted_at: string
}

export interface Post {
  id: string
  url: string
  url_hash: string
  title: string
  content?: string
  source: string
  author?: string
  published_at?: string
  fetched_at: string
  source_metadata?: Record<string, unknown>
  language: string
  is_processed: boolean
}

export interface AnalyticsSummary {
  overview: {
    total_posts: number
    total_ideas: number
    total_clusters: number
    avg_cluster_size: number
    avg_sentiment: number
  }
  trending: {
    hot_clusters: number
    new_ideas_today: number
    new_clusters_this_week: number
  }
  sentiment_distribution: {
    positive: number
    neutral?: number
    negative: number
  }
  top_domains: Array<{
    domain: string
    count: number
  }>
}

export interface TrendDataPoint {
  date: string
  value: number
  avg_sentiment?: number
}

export interface AnalyticsTrends {
  metric: string
  interval: string
  data_points: TrendDataPoint[]
}

export interface DomainStats {
  domain: string
  idea_count: number
  cluster_count?: number
  avg_sentiment: number
  percentage: number
}

export interface JobStatus<T = unknown> {
  job_id: string
  status:
    | "queued"
    | "pending"
    | "running"
    | "completed"
    | "failed"
    | "retrying"
    | "cancelled"
    | "unknown"
    | "PENDING"
    | "STARTED"
    | "SUCCESS"
    | "FAILURE"
    | "RETRY"
  result?: T
  error?: string
  started_at?: string
  completed_at?: string
}

export interface Pagination {
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface APIResponse<T> {
  data: T
  meta?: {
    page: number
    limit: number
    total: number
  }
}
export interface ClusterQueryParams {
  sort_by?: string
  order?: string
  limit?: number
  offset?: number
  min_size?: number
  q?: string
}

export interface IdeaQueryParams {
  cluster_id?: string
  sentiment?: string
  domain?: string
  min_quality?: number
  sort_by?: 'quality' | 'date' | 'sentiment'
  order?: 'asc' | 'desc'
  limit?: number
  offset?: number
  q?: string // For search
}

export interface AnalyticsTrendsParams {
  metric?: string
  interval?: string
  start_date?: string
  end_date?: string
}

export interface ReclusterParams {
  min_quality?: number
  min_cluster_size?: number
  force?: boolean
}
