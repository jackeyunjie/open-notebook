import apiClient from './client'

export interface SkillType {
  skill_type: string
  name: string
  description: string
  parameters_schema?: Record<string, unknown>
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
  trigger_type: 'manual' | 'scheduled'
  triggered_by?: string
  started_at?: string
  completed_at?: string
  output?: Record<string, unknown>
  error_message?: string
  duration_seconds?: number
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

export interface SchedulerStatus {
  running: boolean
  scheduled_jobs: number
  jobs: Array<{
    job_id: string
    skill_instance_id: string
    next_run_time?: string
    trigger: string
  }>
}

export const skillsApi = {
  // Skill Types
  listTypes: async () => {
    const response = await apiClient.get<SkillType[]>('/skills/available')
    return response.data
  },

  // Skill Instances
  listInstances: async () => {
    const response = await apiClient.get<SkillInstance[]>('/skills/instances')
    return response.data
  },

  getInstance: async (id: string) => {
    const response = await apiClient.get<SkillInstance>(`/skills/instances/${id}`)
    return response.data
  },

  createInstance: async (data: CreateSkillInstanceRequest) => {
    const response = await apiClient.post<SkillInstance>('/skills/instances', data)
    return response.data
  },

  updateInstance: async (id: string, data: UpdateSkillInstanceRequest) => {
    const response = await apiClient.patch<SkillInstance>(`/skills/instances/${id}`, data)
    return response.data
  },

  deleteInstance: async (id: string) => {
    const response = await apiClient.delete(`/skills/instances/${id}`)
    return response.data
  },

  executeInstance: async (id: string) => {
    const response = await apiClient.post<{
      execution_id: string
      status: string
      message: string
    }>(`/skills/instances/${id}/execute`)
    return response.data
  },

  // Executions
  listExecutions: async () => {
    const response = await apiClient.get<SkillExecution[]>('/skills/executions')
    return response.data
  },

  getExecution: async (id: string) => {
    const response = await apiClient.get<SkillExecution>(`/skills/executions/${id}`)
    return response.data
  },

  cancelExecution: async (id: string) => {
    const response = await apiClient.post(`/skills/executions/${id}/cancel`)
    return response.data
  },

  // Scheduler
  getSchedulerStatus: async () => {
    const response = await apiClient.get<SchedulerStatus>('/skills/scheduler/status')
    return response.data
  },

  getInstanceSchedule: async (id: string) => {
    const response = await apiClient.get<{
      skill_instance_id: string
      schedule?: string
      next_run_time?: string
      enabled: boolean
    }>(`/skills/instances/${id}/schedule`)
    return response.data
  },

  rescheduleInstance: async (id: string, schedule: string) => {
    const response = await apiClient.post(`/skills/instances/${id}/reschedule`, { schedule })
    return response.data
  },
}
