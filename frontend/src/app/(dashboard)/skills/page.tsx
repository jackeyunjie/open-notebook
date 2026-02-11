'use client'

import { useState } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Plus, RefreshCw, Play, Clock, Settings, Trash2 } from 'lucide-react'
import { useSkillInstances, useExecuteSkillInstance, useDeleteSkillInstance } from '@/lib/hooks/use-skills'
import { useSchedulerStatus } from '@/lib/hooks/use-skills'
import { CreateSkillDialog } from './components/CreateSkillDialog'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/lib/hooks/use-toast'
import Link from 'next/link'

export default function SkillsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const { data: instances, isLoading, refetch } = useSkillInstances()
  const { data: schedulerStatus } = useSchedulerStatus()
  const executeMutation = useExecuteSkillInstance()
  const deleteMutation = useDeleteSkillInstance()
  const { toast } = useToast()

  const handleExecute = async (id: string) => {
    try {
      await executeMutation.mutateAsync(id)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this skill instance?')) {
      return
    }
    try {
      await deleteMutation.mutateAsync(id)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const getSkillTypeBadge = (skillType: string) => {
    const colors: Record<string, string> = {
      rss_crawler: 'bg-blue-100 text-blue-800',
      browser_crawler: 'bg-purple-100 text-purple-800',
      browser_task: 'bg-indigo-100 text-indigo-800',
      browser_monitor: 'bg-pink-100 text-pink-800',
      note_summarizer: 'bg-green-100 text-green-800',
      note_tagger: 'bg-yellow-100 text-yellow-800',
    }
    return colors[skillType] || 'bg-gray-100 text-gray-800'
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">Skills</h1>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Skill
            </Button>
          </div>

          {/* Scheduler Status */}
          {schedulerStatus && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Scheduler Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm">{schedulerStatus.running ? 'Running' : 'Stopped'}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {schedulerStatus.scheduled_jobs} scheduled job{schedulerStatus.scheduled_jobs !== 1 ? 's' : ''}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Skill Instances */}
          <div className="space-y-4">
            {isLoading ? (
              <div className="text-center py-8">Loading...</div>
            ) : instances?.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <p className="text-muted-foreground mb-4">No skill instances yet</p>
                  <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create your first skill
                  </Button>
                </CardContent>
              </Card>
            ) : (
              instances?.map((instance) => (
                <Card key={instance.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{instance.name}</CardTitle>
                          <Badge className={getSkillTypeBadge(instance.skill_type)}>
                            {instance.skill_type}
                          </Badge>
                          {instance.enabled ? (
                            <Badge variant="default" className="bg-green-100 text-green-800">Enabled</Badge>
                          ) : (
                            <Badge variant="secondary">Disabled</Badge>
                          )}
                        </div>
                        {instance.description && (
                          <CardDescription>{instance.description}</CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch checked={instance.enabled} disabled />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        {instance.schedule && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>{instance.schedule}</span>
                          </div>
                        )}
                        {instance.target_notebook_id && (
                          <div>
                            Target: {instance.target_notebook_id}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleExecute(instance.id)}
                          disabled={executeMutation.isPending || !instance.enabled}
                        >
                          <Play className="h-4 w-4 mr-1" />
                          Run
                        </Button>
                        <Link href={`/skills/${instance.id}`}>
                          <Button variant="outline" size="sm">
                            <Settings className="h-4 w-4 mr-1" />
                            Edit
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(instance.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      <CreateSkillDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </AppShell>
  )
}
