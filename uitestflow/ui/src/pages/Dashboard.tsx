import { testApi } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { StatsCard } from '@/components/StatsCard'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  TestTube,
  PlayCircle,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { formatDate, formatDuration } from '@/lib/utils'
import { Link } from 'react-router-dom'

export function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await testApi.getDashboardStats()
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your UI testing activity
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Tests"
          value={stats?.total_tests || 0}
          icon={TestTube}
          description="Active test definitions"
        />
        <StatsCard
          title="Test Runs"
          value={stats?.total_runs || 0}
          icon={PlayCircle}
          description="All time executions"
        />
        <StatsCard
          title="Pass Rate"
          value={`${Math.round((stats?.pass_rate || 0) * 100)}%`}
          icon={TrendingUp}
          description="Success rate"
        />
        <StatsCard
          title="Avg Duration"
          value={formatDuration(stats?.avg_duration_ms || 0)}
          icon={Clock}
          description="Per test execution"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Test Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {!stats?.recent_runs || stats.recent_runs.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No recent test runs
              </p>
            ) : (
              <div className="space-y-2">
                {stats.recent_runs.slice(0, 5).map((run) => (
                  <Link
                    key={run.id}
                    to={`/results/${run.id}`}
                    className="block p-3 rounded-lg border hover:border-primary transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {run.result?.passed ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600" />
                        )}
                        <div>
                          <p className="text-sm font-medium">
                            Test {run.test_id.slice(0, 8)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(run.started_at || run.created_at || '')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={run.result?.passed ? 'default' : 'destructive'}
                        >
                          {run.status}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          {run.duration_ms && formatDuration(run.duration_ms)}
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <div className="mt-4">
              <Button variant="outline" className="w-full" asChild>
                <Link to="/results">View All Results</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Flaky Tests</CardTitle>
          </CardHeader>
          <CardContent>
            {!stats?.flaky_tests || stats.flaky_tests.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No flaky tests detected
              </p>
            ) : (
              <div className="space-y-2">
                {stats.flaky_tests.slice(0, 5).map((test) => (
                  <div
                    key={test.test_id}
                    className="p-3 rounded-lg border"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">{test.test_name}</p>
                        <p className="text-xs text-muted-foreground">
                          ID: {test.test_id.slice(0, 8)}
                        </p>
                      </div>
                      <Badge variant="destructive">
                        {Math.round(test.flakiness_score * 100)}% flaky
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pass Rate Trend (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.trends ? (
              <PassRateTrendChart data={stats.trends} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No trend data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Test Duration Trend</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.trends ? (
              <DurationTrendChart runs={stats.recent_runs || []} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No duration data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Failing Tests</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.flaky_tests && stats.flaky_tests.length > 0 ? (
              <TopFailingTestsChart tests={stats.flaky_tests} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No failing tests
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Test Execution Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.trends ? (
              <ExecutionTimelineChart data={stats.trends} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No execution data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Chart Components
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface TrendData {
  dates: string[]
  passed: number[]
  failed: number[]
}

function PassRateTrendChart({ data }: { data: TrendData }) {
  const chartData = data.dates.map((date, index) => {
    const total = data.passed[index] + data.failed[index]
    const passRate = total > 0 ? (data.passed[index] / total) * 100 : 0
    return {
      date: new Date(date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      passRate: Math.round(passRate),
      passed: data.passed[index],
      failed: data.failed[index],
    }
  })

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          domain={[0, 100]}
          label={{ value: 'Pass Rate (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="passRate"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={{ fill: 'hsl(var(--primary))' }}
          name="Pass Rate (%)"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function DurationTrendChart({ runs }: { runs: any[] }) {
  const chartData = runs
    .slice(0, 10)
    .reverse()
    .map((run) => ({
      id: run.id.slice(0, 6),
      duration: run.duration_ms ? Math.round(run.duration_ms / 1000) : 0,
    }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="id"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          label={{ value: 'Duration (s)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Area
          type="monotone"
          dataKey="duration"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.3}
          name="Duration (seconds)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function TopFailingTestsChart({ tests }: { tests: any[] }) {
  const chartData = tests.slice(0, 5).map((test) => ({
    name: test.test_name.length > 15
      ? test.test_name.slice(0, 15) + '...'
      : test.test_name,
    flakiness: Math.round(test.flakiness_score * 100),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis type="number" className="text-xs" tick={{ fill: 'currentColor' }} />
        <YAxis
          type="category"
          dataKey="name"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          width={120}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Bar
          dataKey="flakiness"
          fill="hsl(var(--destructive))"
          name="Flakiness %"
          radius={[0, 8, 8, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

function ExecutionTimelineChart({ data }: { data: TrendData }) {
  const chartData = data.dates.map((date, index) => ({
    date: new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    passed: data.passed[index],
    failed: data.failed[index],
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis className="text-xs" tick={{ fill: 'currentColor' }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="passed"
          stackId="1"
          stroke="#22c55e"
          fill="#22c55e"
          fillOpacity={0.6}
          name="Passed"
        />
        <Area
          type="monotone"
          dataKey="failed"
          stackId="1"
          stroke="#ef4444"
          fill="#ef4444"
          fillOpacity={0.6}
          name="Failed"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
