import apiClient from './api-client'

export interface ReportGenerationRequest {
  notebook_id: string
  report_type: 'study_guide' | 'literature_review' | 'research_digest' | 'weekly_trends' | 'concept_map'
  source_ids?: string[]
  title?: string
}

export interface ReportGenerationResponse {
  success: boolean
  note_id: string
  message: string
  report_type: string
}

export interface VisualizationRequest {
  notebook_id: string
  chart_type: 'mindmap' | 'timeline' | 'network' | 'bar_chart' | 'pie_chart'
  source_ids?: string[]
  export_format?: 'html' | 'markdown'
}

export interface VisualizationResponse {
  success: boolean
  content: string
  chart_type: string
  export_format: string
}

export interface BatchImportRequest {
  notebook_id: string
  import_type: 'folder' | 'urls' | 'zotero' | 'mendeley'
  source_path?: string
  urls?: string[]
  recursive?: boolean
}

export interface BatchImportResponse {
  success: boolean
  total_found: number
  successful: number
  failed: number
  skipped: number
  errors: Array<{ file?: string; url?: string; error: string }>
}

export const skillsApi = {
  /**
   * 生成研究报告
   */
  generateReport: async (request: ReportGenerationRequest): Promise<ReportGenerationResponse> => {
    const response = await apiClient.post('/api/v1/skills/reports/generate', request)
    return response.data
  },

  /**
   * 创建可视化图表
   */
  createVisualization: async (request: VisualizationRequest): Promise<VisualizationResponse> => {
    const response = await apiClient.post('/api/v1/skills/visualizations/create', request)
    return response.data
  },

  /**
   * 批量导入
   */
  batchImport: async (request: BatchImportRequest): Promise<BatchImportResponse> => {
    const response = await apiClient.post('/api/v1/skills/import/batch', request)
    return response.data
  },

  /**
   * 执行跨文档分析
   */
  analyzeDocuments: async (notebookId: string, analysisType: string, sourceIds?: string[]) => {
    const response = await apiClient.post('/api/v1/skills/analysis/execute', {
      notebook_id: notebookId,
      analysis_type: analysisType,
      source_ids: sourceIds,
    })
    return response.data
  },

  /**
   * 获取可用 UI 操作
   */
  getUIActions: async () => {
    const response = await apiClient.get('/api/v1/skills/ui/actions')
    return response.data
  },

  /**
   * 执行 UI 操作
   */
  executeAction: async (actionType: string, params: any) => {
    const response = await apiClient.post('/api/v1/skills/ui/execute', null, {
      params: { action_type: actionType, ...params },
    })
    return response.data
  },

  /**
   * 获取任务进度
   */
  getTaskProgress: async (taskId: string) => {
    const response = await apiClient.get(`/api/v1/skills/tasks/${taskId}/progress`)
    return response.data
  },

  /**
   * 共享 Notebook
   */
  shareNotebook: async (notebookId: string, ownerId: string, userId: string, permission: string) => {
    const response = await apiClient.post('/api/v1/skills/collaboration/share', {
      notebook_id: notebookId,
      owner_id: ownerId,
      user_id: userId,
      permission: permission,
    })
    return response.data
  },

  /**
   * 获取协作者列表
   */
  getCollaborators: async (notebookId: string) => {
    const response = await apiClient.get(`/api/v1/skills/collaboration/${notebookId}/collaborators`)
    return response.data
  },

  /**
   * 添加评论
   */
  addComment: async (notebookId: string, userId: string, content: string, targetType?: string, targetId?: string) => {
    const response = await apiClient.post('/api/v1/skills/collaboration/comments/add', {
      notebook_id: notebookId,
      user_id: userId,
      content: content,
      target_type: targetType,
      target_id: targetId,
    })
    return response.data
  },

  /**
   * 获取评论
   */
  getComments: async (notebookId: string, targetType?: string, targetId?: string) => {
    const response = await apiClient.get(`/api/v1/skills/collaboration/${notebookId}/comments`, {
      params: { target_type: targetType, target_id: targetId },
    })
    return response.data
  },

  /**
   * 获取性能报告
   */
  getPerformanceReport: async () => {
    const response = await apiClient.get('/api/v1/skills/performance/report')
    return response.data
  },

  /**
   * 健康检查
   */
  healthCheck: async () => {
    const response = await apiClient.get('/api/v1/skills/health')
    return response.data
  },
}
