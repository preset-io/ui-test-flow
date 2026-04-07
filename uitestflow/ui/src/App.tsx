import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Dashboard } from '@/pages/Dashboard'
import { TestLibrary } from '@/pages/TestLibrary'
import { TestRunner } from '@/pages/TestRunner'
import { TestResults } from '@/pages/TestResults'
import { ResultsList } from '@/pages/ResultsList'
import { TestEditor } from '@/pages/TestEditor'
import { Profiles } from '@/pages/Profiles'
import { MCPTestGenerator } from '@/components/MCPTestGenerator'
import { TestExecutionView } from '@/components/TestExecutionView'
import {
  LayoutDashboard,
  TestTube,
  PlayCircle,
  BarChart3,
  Settings,
  Moon,
  Sun,
  Wand2,
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function Navigation() {
  const location = useLocation()
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    const isDark = localStorage.getItem('darkMode') === 'true'
    setDarkMode(isDark)
    if (isDark) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleDarkMode = () => {
    const newMode = !darkMode
    setDarkMode(newMode)
    localStorage.setItem('darkMode', String(newMode))
    if (newMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/library', label: 'Tests', icon: TestTube },
    { path: '/generate', label: 'AI Generate', icon: Wand2 },
    { path: '/runner', label: 'Run Test', icon: PlayCircle },
    { path: '/results', label: 'Results', icon: BarChart3 },
    { path: '/profiles', label: 'Profiles', icon: Settings },
  ]

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <TestTube className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold">UITestFlow</span>
            </Link>
            <div className="flex gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path ||
                  (item.path !== '/' && location.pathname.startsWith(item.path))
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
          >
            {darkMode ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </nav>
  )
}

function AppContent() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/library" element={<TestLibrary />} />
          <Route path="/generate" element={<MCPTestGenerator />} />
          <Route path="/tests/new" element={<TestEditor />} />
          <Route path="/tests/:id/edit" element={<TestEditor />} />
          <Route path="/tests/:testId/execute" element={<TestExecutionView />} />
          <Route path="/runner" element={<TestRunner />} />
          <Route path="/results" element={<ResultsList />} />
          <Route path="/results/:runId" element={<TestResults />} />
          <Route path="/profiles" element={<Profiles />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
