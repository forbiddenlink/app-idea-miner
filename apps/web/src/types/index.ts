// Type definitions for API responses

export interface Cluster {
  id: string;
  label: string;
  description?: string;
  keywords: string[];
  idea_count: number;
  avg_sentiment: number;
  quality_score: number;
  trend_score: number;
  created_at: string;
  updated_at: string;
  evidence?: Idea[];
  related_clusters?: RelatedCluster[];
}

export interface RelatedCluster {
  id: string;
  label: string;
  idea_count: number;
  similarity_score?: number;
}

export interface Idea {
  id: string;
  raw_post_id: string;
  problem_statement: string;
  context?: string;
  sentiment: "positive" | "neutral" | "negative";
  sentiment_score: number;
  emotions?: {
    frustration?: number;
    hope?: number;
    urgency?: number;
  };
  domain?: string;
  features_mentioned?: string[];
  quality_score: number;
  cluster_id?: string;
  cluster?: {
    id: string;
    label: string;
  };
  source_url?: string;
  source?: string;
  raw_post?: {
    id?: string;
    url?: string;
    title?: string;
    source?: string;
    published_at?: string;
  };
  extracted_at: string;
}

export interface AnalyticsSummary {
  overview: {
    total_posts: number;
    total_ideas: number;
    total_clusters: number;
    avg_cluster_size: number;
    avg_sentiment: number;
  };
  trending: {
    hot_clusters: number;
    new_ideas_today: number;
    new_clusters_this_week: number;
  };
  sentiment_distribution: {
    positive: number;
    neutral?: number;
    negative: number;
  };
  top_domains: Array<{
    domain: string;
    count: number;
  }>;
}

export interface TrendDataPoint {
  date: string;
  value: number;
  avg_sentiment?: number;
}

export interface AnalyticsTrends {
  metric: string;
  interval: string;
  data_points: TrendDataPoint[];
}

export interface DomainStats {
  domain: string;
  idea_count: number;
  cluster_count?: number;
  avg_sentiment: number;
  percentage: number;
}

export interface JobStatus<T = unknown> {
  job_id: string;
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
    | "RETRY";
  result?: T;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Pagination {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ClusterQueryParams {
  sort_by?: string;
  order?: string;
  limit?: number;
  offset?: number;
  min_size?: number;
  q?: string;
}

export interface IdeaQueryParams {
  cluster_id?: string;
  sentiment?: string;
  domain?: string;
  min_quality?: number;
  sort_by?: "quality" | "date" | "sentiment";
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
  q?: string; // For search
}

export interface AnalyticsTrendsParams {
  metric?: string;
  interval?: string;
  start_date?: string;
  end_date?: string;
  days?: number;
}

export interface ReclusterParams {
  min_quality?: number;
  min_cluster_size?: number;
  force?: boolean;
}

export interface OpportunityScoreBreakdown {
  score: number;
  max: number;
  description: string;
}

export interface OpportunityScore {
  total: number;
  grade: "A" | "B" | "C" | "D" | "F";
  verdict: string;
  breakdown: {
    demand: OpportunityScoreBreakdown;
    sentiment: OpportunityScoreBreakdown;
    quality: OpportunityScoreBreakdown;
    trend: OpportunityScoreBreakdown;
    diversity: OpportunityScoreBreakdown;
  };
}

export interface Opportunity {
  cluster_id: string;
  cluster_label: string;
  keywords: string[];
  idea_count: number;
  opportunity_score: OpportunityScore;
}

export interface OpportunityQueryParams {
  limit?: number;
  offset?: number;
  min_score?: number;
  sort_by?: "score" | "demand" | "trend";
}

export type BookmarkItemType = "cluster" | "idea";

export interface BookmarkCluster {
  id: string;
  label: string;
  description?: string | null;
  keywords: string[];
  idea_count: number;
  avg_sentiment?: number | null;
  quality_score?: number | null;
  trend_score?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface BookmarkIdea {
  id: string;
  problem_statement: string;
  context?: string | null;
  domain?: string | null;
  sentiment: "positive" | "neutral" | "negative";
  sentiment_score: number;
  emotions?: {
    frustration?: number;
    hope?: number;
    urgency?: number;
  } | null;
  quality_score: number;
  features_mentioned?: string[] | null;
  extracted_at?: string | null;
  raw_post?: {
    id?: string;
    url?: string;
    title?: string;
    source?: string;
    published_at?: string;
  } | null;
}

export interface BookmarkItem {
  item_type: BookmarkItemType;
  item_id: string;
  scope_key: string;
  created_at: string;
  cluster?: BookmarkCluster | null;
  idea?: BookmarkIdea | null;
}

export interface BookmarkListResponse {
  bookmarks: BookmarkItem[];
  pagination: Pagination;
}

export interface BookmarkCreateRequest {
  item_type: BookmarkItemType;
  item_id: string;
}

export interface BookmarkQueryParams {
  item_type?: BookmarkItemType;
  limit?: number;
  offset?: number;
}

export interface BookmarkMutationResponse {
  success: boolean;
  message: string;
}

export interface BookmarkClearResponse {
  success: boolean;
  deleted: number;
}

export type SavedSearchAlertFrequency = "daily" | "weekly";

export interface SavedSearchItem {
  id: string;
  name: string;
  query_params: Record<string, unknown>;
  alert_enabled: boolean;
  alert_frequency: SavedSearchAlertFrequency;
  created_at: string;
  updated_at: string;
}

export interface SavedSearchListResponse {
  saved_searches: SavedSearchItem[];
  pagination: Pagination;
}

export interface SavedSearchCreateRequest {
  name: string;
  query_params?: Record<string, unknown>;
  alert_enabled?: boolean;
  alert_frequency?: SavedSearchAlertFrequency;
}

export interface SavedSearchUpdateRequest {
  name?: string;
  query_params?: Record<string, unknown>;
  alert_enabled?: boolean;
  alert_frequency?: SavedSearchAlertFrequency;
}

export interface SavedSearchQueryParams {
  limit?: number;
  offset?: number;
}

export interface SavedSearchMutationResponse {
  success: boolean;
  message: string;
  saved_search?: SavedSearchItem | null;
}
