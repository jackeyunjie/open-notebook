import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillsApi } from '@/lib/api/skills'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'

// Skill Types
export function useSkillTypes() {
  return useQuery({
    queryKey: QUERY_KEYS.skillTypes,
    queryFn: () => skillsApi.listTypes(),
  })
}

// Skill Instances
export function useSkillInstances() {
  return useQuery({
    queryKey: QUERY_KEYS.skillInstances,
    queryFn: () => skillsApi.listInstances(),
  })
}

export function useSkillInstance(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.skillInstance(id),
    queryFn: () => skillsApi.getInstance(id),
    enabled: !!id,
  })
}

export function useCreateSkillInstance() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: skillsApi.createInstance,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillInstances })
      toast({
        title: t.common.success,
        description: 'Skill instance created successfully',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useUpdateSkillInstance() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof skillsApi.updateInstance>[1] }) =>
      skillsApi.updateInstance(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillInstances })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillInstance(id) })
      toast({
        title: t.common.success,
        description: 'Skill instance updated successfully',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteSkillInstance() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: skillsApi.deleteInstance,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillInstances })
      toast({
        title: t.common.success,
        description: 'Skill instance deleted successfully',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useExecuteSkillInstance() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: skillsApi.executeInstance,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillExecutions })
      toast({
        title: t.common.success,
        description: 'Skill execution started',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

// Executions
export function useSkillExecutions() {
  return useQuery({
    queryKey: QUERY_KEYS.skillExecutions,
    queryFn: () => skillsApi.listExecutions(),
  })
}

export function useSkillExecution(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.skillExecution(id),
    queryFn: () => skillsApi.getExecution(id),
    enabled: !!id,
  })
}

export function useCancelSkillExecution() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: skillsApi.cancelExecution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillExecutions })
      toast({
        title: t.common.success,
        description: 'Execution cancelled',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

// Scheduler
export function useSchedulerStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.schedulerStatus,
    queryFn: () => skillsApi.getSchedulerStatus(),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useSkillInstanceSchedule(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.skillInstanceSchedule(id),
    queryFn: () => skillsApi.getInstanceSchedule(id),
    enabled: !!id,
  })
}

export function useRescheduleSkillInstance() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, schedule }: { id: string; schedule: string }) =>
      skillsApi.rescheduleInstance(id, schedule),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.skillInstanceSchedule(id) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.schedulerStatus })
      toast({
        title: t.common.success,
        description: 'Schedule updated successfully',
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}
