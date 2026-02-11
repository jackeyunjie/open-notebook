'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { skillsApi, SkillInstance, SkillInfo, SchedulerStatus } from '@/lib/api/skills'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useTranslation } from '@/lib/hooks/use-translation'
import { toast } from 'sonner'
import {
  Play,
  Pause,
  Clock,
  Trash2,
  Plus,
  Settings,
  Zap,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function SkillsPage() {
  const { t, language } = useTranslation()
  const router = useRouter()
  const [instances, setInstances] = useState<SkillInstance[]>([])
  const [availableSkills, setAvailableSkills] = useState<SkillInfo[]>([])
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [selectedSkill, setSelectedSkill] = useState<string>('')
  const [newInstanceName, setNewInstanceName] = useState('')
  const [newInstanceDesc, setNewInstanceDesc] = useState('')
  const [newInstanceSchedule, setNewInstanceSchedule] = useState('')
  const [newInstanceParams, setNewInstanceParams] = useState('{}')
  const [executingId, setExecutingId] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [instancesData, skillsData, statusData] = await Promise.all([
        skillsApi.listInstances(),
        skillsApi.listAvailable(),
        skillsApi.getSchedulerStatus(),
      ])
      setInstances(instancesData)
      setAvailableSkills(skillsData)
      setSchedulerStatus(statusData)
    } catch (err) {
      console.error('Failed to fetch skills data:', err)
      toast.error('Failed to load skills data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreateInstance = async () => {
    if (!selectedSkill || !newInstanceName) {
      toast.error('Please fill in required fields')
      return
    }

    try {
      let parameters = {}
      try {
        parameters = JSON.parse(newInstanceParams)
      } catch {
        toast.error('Invalid JSON in parameters')
        return
      }

      await skillsApi.createInstance({
        name: newInstanceName,
        skill_type: selectedSkill,
        description: newInstanceDesc,
        schedule: newInstanceSchedule || undefined,
        parameters,
        enabled: true,
      })

      toast.success('Skill instance created')
      setCreateDialogOpen(false)
      setSelectedSkill('')
      setNewInstanceName('')
      setNewInstanceDesc('')
      setNewInstanceSchedule('')
      setNewInstanceParams('{}')
      fetchData()
    } catch (err) {
      console.error('Failed to create skill instance:', err)
      toast.error('Failed to create skill instance')
    }
  }

  const handleToggleEnabled = async (instance: SkillInstance) => {
    try {
      await skillsApi.updateInstance(instance.id, {
        enabled: !instance.enabled,
      })
      toast.success(instance.enabled ? 'Skill disabled' : 'Skill enabled')
      fetchData()
    } catch (err) {
      console.error('Failed to toggle skill:', err)
      toast.error('Failed to update skill')
    }
  }

  const handleExecute = async (instance: SkillInstance) => {
    try {
      setExecutingId(instance.id)
      const result = await skillsApi.executeInstance(instance.id)
      toast.success(`Skill execution ${result.status}: ${result.message}`)
      fetchData()
    } catch (err) {
      console.error('Failed to execute skill:', err)
      toast.error('Failed to execute skill')
    } finally {
      setExecutingId(null)
    }
  }

  const handleDelete = async (instance: SkillInstance) => {
    if (!confirm(`Are you sure you want to delete "${instance.name}"?`)) {
      return
    }

    try {
      await skillsApi.deleteInstance(instance.id)
      toast.success('Skill instance deleted')
      fetchData()
    } catch (err) {
      console.error('Failed to delete skill instance:', err)
      toast.error('Failed to delete skill instance')
    }
  }

  const getSkillIcon = (skillType: string) => {
    if (skillType.includes('crawler')) return <RefreshCw className="h-4 w-4" />
    if (skillType.includes('browser')) return <Zap className="h-4 w-4" />
    if (skillType.includes('summarizer') || skillType.includes('tagger')) return <Settings className="h-4 w-4" />
    return <Zap className="h-4 w-4" />
  }

  const getStatusBadge = (instance: SkillInstance) => {
    if (!instance.enabled) {
      return (
        <Badge variant="secondary" className="gap-1">
          <Pause className="h-3 w-3" />
          Disabled
        </Badge>
      )
    }
    if (instance.schedule) {
      const job = schedulerStatus?.jobs.find(j => j.skill_instance_id === instance.id.replace('skill_instance:', ''))
      if (job) {
        return (
          <Badge variant="default" className="gap-1 bg-green-600">
            <Clock className="h-3 w-3" />
            Scheduled
          </Badge>
        )
      }
    }
    return (
      <Badge variant="outline" className="gap-1">
        <CheckCircle2 className="h-3 w-3" />
        Active
      </Badge>
    )
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <LoadingSpinner />
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Skills</h1>
            <p className="mt-2 text-muted-foreground">
              Manage automated skills for content crawling, processing, and organization
            </p>
          </div>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Create Skill
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create Skill Instance</DialogTitle>
                <DialogDescription>
                  Configure an automated skill to run on a schedule or manually
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="skill-type">Skill Type *</Label>
                  <Select value={selectedSkill} onValueChange={setSelectedSkill}>
                    <SelectTrigger id="skill-type">
                      <SelectValue placeholder="Select a skill type" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableSkills.map((skill) => (
                        <SelectItem key={skill.skill_type} value={skill.skill_type}>
                          <div className="flex items-center gap-2">
                            {getSkillIcon(skill.skill_type)}
                            {skill.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedSkill && (
                    <p className="text-sm text-muted-foreground">
                      {availableSkills.find(s => s.skill_type === selectedSkill)?.description}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={newInstanceName}
                    onChange={(e) => setNewInstanceName(e.target.value)}
                    placeholder="e.g., Daily News Crawler"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newInstanceDesc}
                    onChange={(e) => setNewInstanceDesc(e.target.value)}
                    placeholder="What does this skill do?"
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule">
                    Schedule (Cron Expression)
                    <span className="text-muted-foreground font-normal ml-2">- Optional</span>
                  </Label>
                  <Input
                    id="schedule"
                    value={newInstanceSchedule}
                    onChange={(e) => setNewInstanceSchedule(e.target.value)}
                    placeholder="e.g., 0 9 * * * (daily at 9am)"
                  />
                  <p className="text-xs text-muted-foreground">
                    Leave empty for manual execution only. Format: minute hour day month weekday
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="parameters">Parameters (JSON)</Label>
                  <Textarea
                    id="parameters"
                    value={newInstanceParams}
                    onChange={(e) => setNewInstanceParams(e.target.value)}
                    placeholder='{"feed_urls": ["https://example.com/rss"], "max_items": 5}'
                    rows={3}
                    className="font-mono text-sm"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateInstance}>Create</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Scheduler Status */}
        {schedulerStatus && (
          <div className="mb-6 rounded-lg border bg-muted/50 p-4">
            <div className="flex items-center gap-4">
              <div className={`h-3 w-3 rounded-full ${schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
              <div className="flex-1">
                <p className="font-medium">
                  Scheduler {schedulerStatus.running ? 'Running' : 'Stopped'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {schedulerStatus.scheduled_jobs} scheduled job{schedulerStatus.scheduled_jobs !== 1 ? 's' : ''}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={fetchData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Instances List */}
        {instances.length === 0 ? (
          <EmptyState
            icon={Zap}
            title="No skill instances yet"
            description="Create your first skill to automate content crawling and processing"
          />
        ) : (
          <div className="space-y-4">
            {instances.map((instance) => (
              <div
                key={instance.id}
                className="rounded-lg border p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="mt-1">{getSkillIcon(instance.skill_type)}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{instance.name}</h3>
                        {getStatusBadge(instance)}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {instance.description || 'No description'}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                        <span className="capitalize">{instance.skill_type.replace(/_/g, ' ')}</span>
                        {instance.schedule && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {instance.schedule}
                          </span>
                        )}
                        {instance.created && (
                          <span>
                            Created {formatDistanceToNow(new Date(instance.created), { addSuffix: true })}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={instance.enabled}
                      onCheckedChange={() => handleToggleEnabled(instance)}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleExecute(instance)}
                      disabled={!instance.enabled || executingId === instance.id}
                    >
                      {executingId === instance.id ? (
                        <LoadingSpinner className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(instance)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
