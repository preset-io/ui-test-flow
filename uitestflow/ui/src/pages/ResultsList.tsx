import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { testApi } from '@/lib/api'
import { TestRun } from '@/types'
import { formatDate, formatDuration, getStatusBadgeVariant } from '@/lib/utils'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Download,
  Filter,
  Search,
  ArrowUpDown,
  CheckCircle2,
  XCircle,
} from 'lucide-react'

const columnHelper = createColumnHelper<TestRun>()

export function ResultsList() {
  const navigate = useNavigate()
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'started_at', desc: true },
  ])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [dateRange, setDateRange] = useState<string>('7d')

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['test-runs', statusFilter, dateRange],
    queryFn: async () => {
      const params: any = {}
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const response = await testApi.getRuns(params)
      // API returns { runs: [], total: 0, page: 1, page_size: 20 }
      return (response.data as any)?.runs || []
    },
  })

  const columns = [
    columnHelper.accessor('result.passed', {
      id: 'status',
      header: ({ column }) => (
        <div className="flex items-center gap-2">
          Status
          <Button
            variant="ghost"
            size="sm"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 w-8 p-0"
          >
            <ArrowUpDown className="h-4 w-4" />
          </Button>
        </div>
      ),
      cell: ({ row }) => {
        const passed = row.original.result?.passed
        const status = row.original.status
        return (
          <div className="flex items-center gap-2">
            {status === 'completed' && (
              <>
                {passed ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-600" />
                )}
              </>
            )}
            <Badge variant={getStatusBadgeVariant(status)}>
              {status === 'completed' ? (passed ? 'Passed' : 'Failed') : status}
            </Badge>
          </div>
        )
      },
      sortingFn: (a, b) => {
        const aVal = a.original.result?.passed ? 1 : 0
        const bVal = b.original.result?.passed ? 1 : 0
        return aVal - bVal
      },
    }),
    columnHelper.accessor('test_id', {
      header: 'Test ID',
      cell: ({ getValue }) => (
        <code className="text-xs bg-muted px-2 py-1 rounded">
          {getValue().slice(0, 8)}...
        </code>
      ),
    }),
    columnHelper.accessor('started_at', {
      header: ({ column }) => (
        <div className="flex items-center gap-2">
          Started
          <Button
            variant="ghost"
            size="sm"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 w-8 p-0"
          >
            <ArrowUpDown className="h-4 w-4" />
          </Button>
        </div>
      ),
      cell: ({ getValue, row }) => {
        const started = getValue() || row.original.created_at
        return <span className="text-sm">{formatDate(started || '')}</span>
      },
      sortingFn: (a, b) => {
        const aVal = new Date(
          a.original.started_at || a.original.created_at || 0
        ).getTime()
        const bVal = new Date(
          b.original.started_at || b.original.created_at || 0
        ).getTime()
        return aVal - bVal
      },
    }),
    columnHelper.accessor('duration_ms', {
      header: ({ column }) => (
        <div className="flex items-center gap-2">
          Duration
          <Button
            variant="ghost"
            size="sm"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 w-8 p-0"
          >
            <ArrowUpDown className="h-4 w-4" />
          </Button>
        </div>
      ),
      cell: ({ getValue }) => {
        const duration = getValue()
        return (
          <span className="text-sm">
            {duration ? formatDuration(duration) : '-'}
          </span>
        )
      },
    }),
    columnHelper.accessor('result', {
      id: 'pass_rate',
      header: 'Pass Rate',
      cell: ({ getValue }) => {
        const result = getValue()
        if (!result) return <span className="text-sm text-muted-foreground">-</span>
        const passRate = Math.round(
          (result.steps_passed / result.steps_executed) * 100
        )
        return (
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary"
                style={{ width: `${passRate}%` }}
              />
            </div>
            <span className="text-sm font-medium">{passRate}%</span>
          </div>
        )
      },
    }),
    columnHelper.accessor('profile', {
      header: 'Profile',
      cell: ({ getValue }) => (
        <Badge variant="outline" className="text-xs">
          {getValue()}
        </Badge>
      ),
    }),
    columnHelper.accessor('triggered_by', {
      header: 'Trigger',
      cell: ({ getValue }) => (
        <span className="text-sm text-muted-foreground capitalize">
          {getValue()}
        </span>
      ),
    }),
  ]

  const table = useReactTable({
    data: runs,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  })

  const exportToCSV = () => {
    const headers = ['Status', 'Test ID', 'Started', 'Duration', 'Pass Rate', 'Profile', 'Trigger']
    const rows = runs.map((run: any) => [
      run.status === 'completed' ? (run.result?.passed ? 'Passed' : 'Failed') : run.status,
      run.test_id,
      run.started_at || run.created_at || '',
      run.duration_ms ? formatDuration(run.duration_ms) : '-',
      run.result
        ? `${Math.round((run.result.steps_passed / run.result.steps_executed) * 100)}%`
        : '-',
      run.profile,
      run.triggered_by,
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map((row: any) => row.map((cell: any) => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `test-results-${new Date().toISOString()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading test results...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Test Results</h1>
          <p className="text-muted-foreground">Browse and filter test execution history</p>
        </div>
        <Button onClick={exportToCSV} className="gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search test runs..."
                  value={globalFilter}
                  onChange={(e) => setGlobalFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="aborted">Aborted</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="all">All time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.length > 0 ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/results/${row.original.id}`)}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center text-muted-foreground"
                    >
                      No test results found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between px-4 py-4 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
              {Math.min(
                (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                runs.length
              )}{' '}
              of {runs.length} results
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm">
                Page {table.getState().pagination.pageIndex + 1} of{' '}
                {table.getPageCount()}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                disabled={!table.getCanNextPage()}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
