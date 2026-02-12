import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  async getHealth() {
    const response = await this.client.get('/health')
    return response.data
  }

  // Analytics
  async getAnalyticsSummary() {
    const response = await this.client.get('/api/v1/analytics/summary')
    return response.data
  }

  async getAnalyticsTrends(params: {
    metric?: string
    interval?: string
    start_date?: string
    end_date?: string
  }) {
    const response = await this.client.get('/api/v1/analytics/trends', { params })
    return response.data
  }

  async getAnalyticsDomains() {
    const response = await this.client.get('/api/v1/analytics/domains')
    return response.data
  }

  // Clusters
  async getClusters(params?: {
    sort_by?: string
    order?: string
    limit?: number
    offset?: number
    min_size?: number
  }) {
    const response = await this.client.get('/api/v1/clusters', { params })
    return response.data
  }

  async getCluster(id: string, includeEvidence = true) {
    const response = await this.client.get(`/api/v1/clusters/${id}`, {
      params: { evidence_limit: includeEvidence ? 5 : 0 },
    })
    return response.data
  }

  async getSimilarClusters(id: string, limit = 5) {
    const response = await this.client.get(`/api/v1/clusters/${id}/similar`, {
      params: { limit },
    })
    return response.data
  }

  async getTrendingClusters(limit = 10, minTrendScore = 0.5) {
    const response = await this.client.get('/api/v1/clusters/trending/list', {
      params: { limit, min_trend_score: minTrendScore },
    })
    return response.data
  }

  // Ideas
  async getIdeas(params?: {
    cluster_id?: string
    sentiment?: string
    domain?: string
    min_quality?: number
    limit?: number
    offset?: number
  }) {
    const response = await this.client.get('/api/v1/ideas', { params })
    return response.data
  }

  async getIdeaById(id: string) {
    const response = await this.client.get(`/api/v1/ideas/${id}`)
    return response.data
  }

  async searchIdeas(query: string, limit = 20) {
    const response = await this.client.get('/api/v1/ideas/search/query', {
      params: { q: query, limit },
    })
    return response.data
  }

  // Jobs
  async triggerIngestion() {
    const response = await this.client.post('/api/v1/jobs/ingest', {})
    return response.data
  }

  async triggerClustering(params?: {
    min_quality?: number
    min_cluster_size?: number
    force?: boolean
  }) {
    const response = await this.client.post('/api/v1/jobs/recluster', params || {})
    return response.data
  }

  async getJobStatus(jobId: string) {
    const response = await this.client.get(`/api/v1/jobs/${jobId}`)
    return response.data
  }
}

export const apiClient = new ApiClient()
export default apiClient

// Convenience functions
export const getHealth = () => apiClient.getHealth()
export const getAnalyticsSummary = () => apiClient.getAnalyticsSummary()
export const getAnalyticsTrends = (params: any) => apiClient.getAnalyticsTrends(params)
export const getAnalyticsDomains = () => apiClient.getAnalyticsDomains()
export const getClusters = (params?: any) => apiClient.getClusters(params)
export const getCluster = (id: string, includeEvidence?: boolean) => apiClient.getCluster(id, includeEvidence)
export const getSimilarClusters = (id: string, limit?: number) => apiClient.getSimilarClusters(id, limit)
export const getTrendingClusters = (limit?: number, minTrendScore?: number) => apiClient.getTrendingClusters(limit, minTrendScore)
export const getIdeas = (params?: any) => apiClient.getIdeas(params)
export const getIdeaById = (id: string) => apiClient.getIdeaById(id)
export const searchIdeas = (query: string, limit?: number) => apiClient.searchIdeas(query, limit)
export const triggerIngestion = () => apiClient.triggerIngestion()
export const triggerClustering = (params?: any) => apiClient.triggerClustering(params)
export const getJobStatus = (jobId: string) => apiClient.getJobStatus(jobId)
