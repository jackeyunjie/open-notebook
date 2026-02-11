'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { useSkillTypes, useCreateSkillInstance } from '@/lib/hooks/use-skills'
import { useNotebooks } from '@/lib/hooks/use-notebooks'

interface CreateSkillDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateSkillDialog({ open, onOpenChange }: CreateSkillDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [skillType, setSkillType] = useState('')
  const [enabled, setEnabled] = useState(true)
  const [schedule, setSchedule] = useState('')
  const [targetNotebookId, setTargetNotebookId] = useState('')
  const [parameters, setParameters] = useState('{}')

  const { data: skillTypes, isLoading: typesLoading } = useSkillTypes()
  const { data: notebooks, isLoading: notebooksLoading } = useNotebooks(false)
  const createMutation = useCreateSkillInstance()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const parsedParams = JSON.parse(parameters)
      await createMutation.mutateAsync({
        name,
        skill_type: skillType,
        description: description || undefined,
        enabled,
        parameters: parsedParams,
        schedule: schedule || undefined,
        target_notebook_id: targetNotebookId || undefined,
      })
      onOpenChange(false)
      resetForm()
    } catch (error) {
      // Error handled by mutation
    }
  }

  const resetForm = () => {
    setName('')
    setDescription('')
    setSkillType('')
    setEnabled(true)
    setSchedule('')
    setTargetNotebookId('')
    setParameters('{}')
  }

  const handleClose = () => {
    onOpenChange(false)
    resetForm()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Skill</DialogTitle>
            <DialogDescription>
              Configure a new skill instance for automated tasks.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Daily RSS Feed"
                required
              />
            </div>

            {/* Skill Type */}
            <div className="space-y-2">
              <Label htmlFor="skillType">Skill Type *</Label>
              <Select value={skillType} onValueChange={setSkillType} required>
                <SelectTrigger>
                  <SelectValue placeholder="Select a skill type" />
                </SelectTrigger>
                <SelectContent>
                  {typesLoading ? (
                    <SelectItem value="loading" disabled>Loading...</SelectItem>
                  ) : (
                    skillTypes?.map((type) => (
                      <SelectItem key={type.skill_type} value={type.skill_type}>
                        {type.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {skillType && skillTypes && (
                <p className="text-sm text-muted-foreground">
                  {skillTypes.find(t => t.skill_type === skillType)?.description}
                </p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description of what this skill does"
                rows={2}
              />
            </div>

            {/* Enabled */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="enabled"
                checked={enabled}
                onCheckedChange={(checked) => setEnabled(checked as boolean)}
              />
              <Label htmlFor="enabled" className="cursor-pointer">Enabled</Label>
            </div>

            {/* Schedule */}
            <div className="space-y-2">
              <Label htmlFor="schedule">Schedule (Cron Expression)</Label>
              <Input
                id="schedule"
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
                placeholder="e.g., 0 9 * * * (daily at 9am)"
              />
              <p className="text-sm text-muted-foreground">
                Leave empty for manual execution only. Examples: 0 * * * * (hourly), 0 9 * * * (daily 9am)
              </p>
            </div>

            {/* Target Notebook */}
            <div className="space-y-2">
              <Label htmlFor="notebook">Target Notebook</Label>
              <Select value={targetNotebookId} onValueChange={setTargetNotebookId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a notebook (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {notebooksLoading ? (
                    <SelectItem value="loading" disabled>Loading...</SelectItem>
                  ) : (
                    notebooks?.map((notebook) => (
                      <SelectItem key={notebook.id} value={notebook.id}>
                        {notebook.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Parameters */}
            <div className="space-y-2">
              <Label htmlFor="parameters">Parameters (JSON)</Label>
              <Textarea
                id="parameters"
                value={parameters}
                onChange={(e) => setParameters(e.target.value)}
                placeholder='{"key": "value"}'
                rows={4}
                className="font-mono text-sm"
              />
              <p className="text-sm text-muted-foreground">
                JSON object with parameters for this skill. Example: {"feed_urls": ["https://example.com/rss"], "max_items": 5}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !name || !skillType}>
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
