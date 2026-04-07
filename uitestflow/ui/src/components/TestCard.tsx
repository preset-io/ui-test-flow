import { Play, Edit, Trash2, MoreVertical } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { TestDefinition } from '@/types'
import { formatDate } from '@/lib/utils'

interface TestCardProps {
  test: TestDefinition
  onRun?: () => void
  onEdit?: () => void
  onDelete?: () => void
}

export function TestCard({ test, onRun, onEdit, onDelete }: TestCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl">{test.name}</CardTitle>
            <CardDescription className="mt-1">
              {test.description || 'No description'}
            </CardDescription>
          </div>
          <Button variant="ghost" size="icon">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {test.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="text-sm text-muted-foreground">
            <p>{test.steps.length} steps</p>
            <p>Updated {formatDate(test.updated_at)}</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button onClick={onRun} className="flex-1">
          <Play className="mr-2 h-4 w-4" />
          Run Test
        </Button>
        <Button onClick={onEdit} variant="outline" size="icon">
          <Edit className="h-4 w-4" />
        </Button>
        <Button onClick={onDelete} variant="outline" size="icon">
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  )
}
