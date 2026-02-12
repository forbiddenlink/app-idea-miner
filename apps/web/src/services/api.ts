import axios, { AxiosInstance } from 'axios'
import {
  AnalyticsSummary,
  AnalyticsTrends,
  AnalyticsTrendsParams,
  Cluster,
  ClusterQueryParams,
  DomainStats,
  Idea,
  IdeaQueryParams,
  JobStatus,
  Pagination,
  ReclusterParams,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-api-key'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.request.use((config) => {
      if (API_KEY) {
        config.headers['X-API-Key'] = API_KEY
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 429) {
          console.error('Rate limit exceeded')
        }
        return Promise.reject(error)
      }
    )
  }

  // Health check
  async getHealth(): Promise<{ status: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  // Analytics
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await this.client.get('/api/v1/analytics/summary')
    return response.data
  }

  async getAnalyticsTrends(params: AnalyticsTrendsParams): Promise<AnalyticsTrends> {
    const response = await this.client.get('/api/v1/analytics/trends', { params })
    return response.data
  }

  async getAnalyticsDomains(): Promise<DomainStats[]> {
    const response = await this.client.get('/api/v1/analytics/domains')
    const payload = response.data as {
      domains: Array<{
        name: string
        idea_count: number
        avg_sentiment: number
        percentage: number
      }>
    }

    return (payload.domains || []).map((domain) => ({
      domain: domain.name,
      idea_count: domain.idea_count,
      avg_sentiment: domain.avg_sentiment,
      percentage: domain.percentage,
    }))
  }

  // Clusters
  async getClusters(
    params?: ClusterQueryParams
  ): Promise<{ clusters: Cluster[]; pagination: Pagination }> {
    const response = await this.client.get('/api/v1/clusters', { params })
    return response.data
  }

  async getCluster(id: string, includeEvidence = true): Promise<Cluster> {
    const response = await this.client.get(`/api/v1/clusters/${id}`, {
      params: { evidence_limit: includeEvidence ? 5 : 0 },
    })
    return response.data
  }

  async getSimilarClusters(
    id: string,
    limit = 5
  ): Promise<{ source_cluster: Partial<Cluster>; similar_clusters: Cluster[] }> {
    const response = await this.client.get(`/api/v1/clusters/${id}/similar`, {
      params: { limit },
    })
    return response.data
  }

  async getTrendingClusters(
    limit = 10,
    minTrendScore = 0.5
  ): Promise<{ trending: Cluster[] }> {
    const response = await this.client.get('/api/v1/clusters/trending/list', {
      params: { limit, min_trend_score: minTrendScore },
    })
    return response.data
  }

  // Ideas
  async getIdeas(
    params?: IdeaQueryParams
  ): Promise<{ ideas: Idea[]; pagination: Pagination }> {
    const response = await this.client.get('/api/v1/ideas', { params })
    return response.data
  }

  async getIdeaById(id: string): Promise<Idea> {
    const response = await this.client.get(`/api/v1/ideas/${id}`)
    return response.data
  }

  async searchIdeas(query: string, limit = 20): Promise<{ results: Idea[] }> {
    const response = await this.client.get('/api/v1/ideas/search/query', {
      params: { q: query, limit },
    })
    return response.data
  }

  // Jobs
  async triggerIngestion(): Promise<JobStatus> {
    const response = await this.client.post('/api/v1/jobs/ingest', {})
    return response.data
  }

  async triggerClustering(params?: ReclusterParams): Promise<JobStatus> {
    const response = await this.client.post('/api/v1/jobs/recluster', params || {})
    return response.data
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await this.client.get(`/api/v1/jobs/${jobId}`)
    return response.data
  }
}

export const apiClient = new ApiClient()
export default apiClient

// Convenience functions
export const getHealth = () => apiClient.getHealth()
export const getAnalyticsSummary = () => apiClient.getAnalyticsSummary()
export const getAnalyticsTrends = (params: AnalyticsTrendsParams) => apiClient.getAnalyticsTrends(params)
export const getAnalyticsDomains = () => apiClient.getAnalyticsDomains()
export const getClusters = (params?: ClusterQueryParams) => apiClient.getClusters(params)
export const getCluster = (id: string, includeEvidence?: boolean) => apiClient.getCluster(id, includeEvidence)
export const getSimilarClusters = (id: string, limit?: number) => apiClient.getSimilarClusters(id, limit)
export const getTrendingClusters = (limit?: number, minTrendScore?: number) => apiClient.getTrendingClusters(limit, minTrendScore)
export const getIdeas = (params?: IdeaQueryParams) => apiClient.getIdeas(params)
export const getIdeaById = (id: string) => apiClient.getIdeaById(id)
export const searchIdeas = (query: string, limit?: number) => apiClient.searchIdeas(query, limit)
export const triggerIngestion = () => apiClient.triggerIngestion()
export const triggerClustering = (params?: ReclusterParams) => apiClient.triggerClustering(params)
export const getJobStatus = (jobId: string) => apiClient.getJobStatus(jobId)
