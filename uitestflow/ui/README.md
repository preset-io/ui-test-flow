# UITestFlow React UI

Modern React-based web interface for UITestFlow, built with TypeScript, Vite, and Tailwind CSS.

## Overview

This is the frontend application for UITestFlow, providing a beautiful and intuitive web interface for creating, running, and monitoring UI tests. The application is built with modern web technologies for optimal performance and developer experience.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: TanStack Query (React Query) + Zustand
- **Routing**: React Router v6
- **Charts**: Recharts
- **API Client**: Axios
- **Form Handling**: React Hook Form
- **Schema Validation**: Zod

## Project Structure

```
uitestflow/ui/
├── public/                 # Static assets
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── api/               # API client and hooks
│   │   ├── client.ts
│   │   ├── queries/
│   │   └── mutations/
│   ├── components/        # Reusable components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── layout/       # Layout components
│   │   └── features/     # Feature-specific components
│   ├── pages/            # Page components
│   │   ├── Dashboard/
│   │   ├── Tests/
│   │   ├── Results/
│   │   └── Settings/
│   ├── hooks/            # Custom React hooks
│   ├── store/            # Zustand stores
│   ├── types/            # TypeScript types
│   ├── utils/            # Utility functions
│   ├── styles/           # Global styles
│   ├── App.tsx           # Root component
│   ├── main.tsx          # Entry point
│   └── vite-env.d.ts     # Vite type definitions
├── .env.example          # Environment variables template
├── .eslintrc.js          # ESLint configuration
├── .prettierrc           # Prettier configuration
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── tailwind.config.js    # Tailwind CSS configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)
- UITestFlow backend running (see main README.md)

### Installation

1. **Install dependencies**:

```bash
cd uitestflow/ui
npm install
```

2. **Configure environment**:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# VITE_API_URL=http://localhost:8080
```

3. **Start development server**:

```bash
npm run dev
```

The application will be available at <http://localhost:3000>

### Docker Development

Alternatively, use Docker Compose for development:

```bash
# From project root
docker-compose --profile ui-dev up -d

# View logs
docker-compose logs -f ui
```

## Available Scripts

### Development

```bash
# Start development server with hot reload
npm run dev

# Start with custom host/port
npm run dev -- --host 0.0.0.0 --port 3001
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Run Prettier
npm run format

# Type check
npm run type-check
```

### Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests (Playwright)
npm run test:e2e
```

## Configuration

### Environment Variables

Create a `.env` file in the `ui/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8080
VITE_API_TIMEOUT=30000

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WEBSOCKETS=true

# Authentication
VITE_AUTH_PROVIDER=local  # local, oauth, saml

# Development
VITE_ENABLE_MOCK_API=false
VITE_LOG_LEVEL=info
```

### API Client Configuration

The API client is configured in `src/api/client.ts`:

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: import.meta.env.VITE_API_TIMEOUT || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

## Component Documentation

### UI Components (shadcn/ui)

We use shadcn/ui for consistent, accessible components. Components are located in `src/components/ui/`.

#### Adding New Components

```bash
# Install shadcn/ui CLI (if not already installed)
npm install -D @shadcn/ui

# Add a component (e.g., button)
npx shadcn-ui add button

# Add multiple components
npx shadcn-ui add button card dialog
```

Available components:

- Button, Input, Select, Checkbox, Radio
- Card, Dialog, Sheet, Popover, Dropdown Menu
- Table, Tabs, Accordion, Collapsible
- Alert, Badge, Toast, Progress
- And more...

### Custom Components

#### TestCard Component

Display test information in a card format:

```tsx
import { TestCard } from '@/components/features/TestCard';

<TestCard
  test={test}
  onRun={() => handleRun(test.id)}
  onEdit={() => handleEdit(test.id)}
  onDelete={() => handleDelete(test.id)}
/>
```

#### ScreenshotGallery Component

Display test screenshots in a lightbox gallery:

```tsx
import { ScreenshotGallery } from '@/components/features/ScreenshotGallery';

<ScreenshotGallery
  screenshots={screenshots}
  initialIndex={0}
/>
```

## State Management

### TanStack Query (React Query)

Used for server state management (API data fetching and caching).

Example usage:

```tsx
import { useQuery } from '@tanstack/react-query';
import { getTests } from '@/api/queries/tests';

function TestList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['tests'],
    queryFn: getTests,
  });

  if (isLoading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <div>
      {data.tests.map(test => (
        <TestCard key={test.id} test={test} />
      ))}
    </div>
  );
}
```

### Zustand

Used for client-side state management (UI state, user preferences).

Example store:

```tsx
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
```

## Routing

React Router v6 is used for client-side routing.

Routes are defined in `src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Tests from './pages/Tests';
import Results from './pages/Results';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tests" element={<Tests />} />
        <Route path="/tests/:id" element={<TestDetail />} />
        <Route path="/results" element={<Results />} />
        <Route path="/results/:id" element={<ResultDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Styling

### Tailwind CSS

Tailwind CSS is used for utility-first styling. Configure in `tailwind.config.js`:

```javascript
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          // ... more shades
        },
      },
    },
  },
  plugins: [],
};
```

### Global Styles

Global styles are defined in `src/styles/global.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* ... more CSS variables */
  }
}
```

### Dark Mode

Dark mode is supported using Tailwind's dark mode feature:

```tsx
// Toggle dark mode
function ThemeToggle() {
  const { theme, setTheme } = useUIStore();

  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}
```

## API Integration

### Query Hooks

Create custom hooks for data fetching in `src/api/queries/`:

```tsx
// src/api/queries/tests.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../client';

export function useTests() {
  return useQuery({
    queryKey: ['tests'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/tests');
      return data;
    },
  });
}

export function useTest(id: string) {
  return useQuery({
    queryKey: ['tests', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/tests/${id}`);
      return data;
    },
    enabled: !!id,
  });
}
```

### Mutation Hooks

Create custom hooks for mutations in `src/api/mutations/`:

```tsx
// src/api/mutations/tests.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

export function useCreateTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (testData) => {
      const { data } = await apiClient.post('/api/tests', testData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] });
    },
  });
}
```

## TypeScript

### Type Definitions

Types are defined in `src/types/`:

```tsx
// src/types/test.ts
export interface Test {
  id: string;
  name: string;
  description?: string;
  steps: TestStep[];
  evaluators: Evaluator[];
  createdAt: string;
  updatedAt: string;
}

export interface TestStep {
  name: string;
  action: string;
  selector?: string;
  value?: string;
}

export interface TestResult {
  id: string;
  testId: string;
  status: 'passed' | 'failed' | 'running';
  duration: number;
  screenshots: Screenshot[];
  logs: Log[];
}
```

### Type-Safe API Calls

Use types with API calls:

```tsx
import type { Test, CreateTestInput } from '@/types/test';

async function createTest(input: CreateTestInput): Promise<Test> {
  const { data } = await apiClient.post<Test>('/api/tests', input);
  return data;
}
```

## Testing

### Unit Tests (Vitest)

```tsx
// src/components/TestCard.test.tsx
import { render, screen } from '@testing-library/react';
import { TestCard } from './TestCard';

describe('TestCard', () => {
  it('renders test name', () => {
    const test = { id: '1', name: 'Login Test' };
    render(<TestCard test={test} />);
    expect(screen.getByText('Login Test')).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)

```tsx
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('dashboard displays test list', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.locator('h1')).toHaveText('Dashboard');
  await expect(page.locator('.test-card')).toHaveCount.greaterThan(0);
});
```

## Deployment

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

The build output will be in `dist/` directory.

### Environment-Specific Builds

```bash
# Staging build
VITE_API_URL=https://staging.uitestflow.io npm run build

# Production build
VITE_API_URL=https://api.uitestflow.io npm run build
```

### Static Hosting

The built files can be hosted on any static hosting service:

- **Vercel**: `vercel deploy`
- **Netlify**: `netlify deploy --prod`
- **AWS S3**: Upload `dist/` contents to S3 bucket
- **Nginx**: Serve `dist/` directory

### Docker Deployment

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Performance Optimization

### Code Splitting

Use dynamic imports for route-based code splitting:

```tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Tests = lazy(() => import('./pages/Tests'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tests" element={<Tests />} />
      </Routes>
    </Suspense>
  );
}
```

### Image Optimization

Use optimized image formats and lazy loading:

```tsx
<img
  src={screenshot.url}
  alt={screenshot.name}
  loading="lazy"
  width={800}
  height={600}
/>
```

### Bundle Analysis

```bash
# Analyze bundle size
npm run build -- --report

# Or use vite-bundle-visualizer
npm install -D vite-bundle-visualizer
```

## Contributing

### Code Style

- Follow TypeScript best practices
- Use functional components and hooks
- Maintain consistent file structure
- Write meaningful commit messages

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with clear commit messages
3. Run linter and tests: `npm run lint && npm test`
4. Submit PR with description and screenshots
5. Address review feedback
6. Merge after approval

## Troubleshooting

### Common Issues

**Port already in use**

```bash
# Kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- --port 3001
```

**Module not found errors**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Type errors**

```bash
# Regenerate types
npm run type-check
```

**Build fails**

```bash
# Clear build cache
rm -rf dist .vite
npm run build
```

## Resources

- **Vite Documentation**: <https://vitejs.dev>
- **React Documentation**: <https://react.dev>
- **TypeScript Handbook**: <https://www.typescriptlang.org/docs>
- **Tailwind CSS**: <https://tailwindcss.com>
- **shadcn/ui**: <https://ui.shadcn.com>
- **TanStack Query**: <https://tanstack.com/query>
- **React Router**: <https://reactrouter.com>

## License

Same as main project (Apache 2.0)
