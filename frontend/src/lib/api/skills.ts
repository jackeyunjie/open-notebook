import apiClient from './client'

// Types
export interface SkillInfo {
  skill_type: string
  name: string
  description: string
}

export interface SkillInstance {
  id: string
  name: string
  skill_type: string
  description?: string
  enabled: boolean
  parameters: Record<string, unknown>
  schedule?: string
  target_notebook_id?: string
  created?: string
  updated?: string
}

export interface SkillExecution {
  id: string
  skill_instance_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  trigger_type: string
  triggered_by?: string
  started_at?: string
  completed_at?: string
  output?: Record<string, unknown>
  error_message?: string
  created_source_ids: string[]
  created_note_ids: string[]
  duration_seconds?: number
}

export interface SchedulerStatus {
  running: boolean
  scheduled_jobs: number
  jobs: {
    job_id: string
    skill_instance_id: string
    next_run_time?: string
    trigger: string
  }[]
}

export interface CreateSkillInstanceRequest {
  name: string
  skill_type: string
  description?: string
  enabled?: boolean
  parameters?: Record<string, unknown>
  schedule?: string
  target_notebook_id?: string
}

export interface UpdateSkillInstanceRequest {
  name?: string
  description?: string
  enabled?: boolean
  parameters?: Record<string, unknown>
  schedule?: string
  target_notebook_id?: string
}

export interface ExecuteSkillRequest {
  parameters?: Record<string, unknown>
  trigger_type?: string
}

export interface ExecuteSkillResponse {
  execution_id: string
  status: string
  message: string
}

// API Functions
export const skillsApi = {
  // Available skills
  listAvailable: async (): Promise<SkillInfo[]> => {
    const response = await apiClient.get('/skills/available')
    return response.data
  },

  // Skill instances
  listInstances: async (params?: { skill_type?: string; notebook_id?: string }): Promise<SkillInstance[]> => {
    const response = await apiClient.get('/skills/instances', { params })
    return response.data
  },

  getInstance: async (id: string): Promise<SkillInstance> => {
    const response = await apiClient.get(`/skills/instances/${id}`)
    return response.data
  },

  createInstance: async (data: CreateSkillInstanceRequest): Promise<SkillInstance> => {
    const response = await apiClient.post('/skills/instances', data)
    return response.data
  },

  updateInstance: async (id: string, data: UpdateSkillInstanceRequest): Promise<SkillInstance> => {
    const response = await apiClient.patch(`/skills/instances/${id}`, data)
    return response.data
  },

  deleteInstance: async (id: string): Promise<void> => {
    await apiClient.delete(`/skills/instances/${id}`)
  },

  // Execute skill
  executeInstance: async (id: string, data?: ExecuteSkillRequest): Promise<ExecuteSkillResponse> => {
    const response = await apiClient.post(`/skills/instances/${id}/execute`, data || {})
    return response.data
  },

  executeDirect: async (skill_type: string, parameters: Record<string, unknown>, name?: string): Promise<ExecuteSkillResponse> => {
    const response = await apiClient.post('/skills/execute', {
      skill_type,
      name: name || 'Ad-hoc Execution',
      description: '',
      parameters,
    })
    return response.data
  },

  // Execution history
  listExecutions: async (params?: { instance_id?: string; limit?: number }): Promise<SkillExecution[]> => {
    const response = await apiClient.get('/skills/executions', { params })
    return response.data
  },

  getExecution: async (id: string): Promise<SkillExecution> => {
    const response = await apiClient.get(`/skills/executions/${id}`)
    return response.data
  },

  cancelExecution: async (id: string): Promise<void> => {
    await apiClient.post(`/skills/executions/${id}/cancel`)
  },

  // Scheduler management
  getSchedulerStatus: async (): Promise<SchedulerStatus> => {
    const response = await apiClient.get('/skills/scheduler/status')
    return response.data
  },

  getSkillSchedule: async (instanceId: string): Promise<{
    skill_instance_id: string
    schedule?: string
    next_run_time?: string
    enabled: boolean
  }> => {
    const response = await apiClient.get(`/skills/instances/${instanceId}/schedule`)
    return response.data
  },

  rescheduleSkill: async (instanceId: string, schedule: string): Promise<{ message: string; schedule: string }> => {
    const response = await apiClient.post(`/skills/instances/${instanceId}/reschedule`, { schedule })
    return response.data
  },
}
