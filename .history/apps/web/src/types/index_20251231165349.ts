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
  source_metadata?: Record<string, any>
  language: string
  is_processed: boolean
}

export interface AnalyticsSummary {
  overview: {
    total_posts: number
    total_ideas: number
    total_clusters: number
    avg_cluster_size: string
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

export interface JobStatus {
  job_id: string
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'
  result?: any
  error?: string
  started_at?: string
  completed_at?: string
}
