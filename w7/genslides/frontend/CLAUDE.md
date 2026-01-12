# GenSlides Frontend - Development Guidelines

IMPORTANT: always use latest dependencies. follow design tokens and global.css in ./src/styles/design-tokens.css and ./src/styles/global.css

## Tech Stack

- **Language**: TypeScript
- **Framework**: React 19+
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Drag & Drop**: @dnd-kit

## Architecture Principles

### SOLID Principles (Adapted for React)

- **S - Single Responsibility**: One component, one purpose
  - `SlideList.tsx` - Renders list only, delegates item rendering to `SlideItem`
  - `useSlides.ts` - Data fetching only, no UI logic
  - `slideStore.ts` - State management only, no API calls

- **O - Open/Closed**: Components open for extension via props

  ```tsx
  // Good: extensible via props
  <Button variant="primary" size="lg" onClick={handleClick} />

  // Avoid: modifying component internals for each use case
  ```

- **L - Liskov Substitution**: Components with same interface are interchangeable

  ```tsx
  // Both can be used wherever a clickable element is expected
  <Button onClick={...}>Click</Button>
  <IconButton onClick={...} icon={<PlayIcon />} />
  ```

- **I - Interface Segregation**: Small, focused prop interfaces

  ```tsx
  // Good: focused interface
  interface SlideItemProps {
    slide: Slide;
    isSelected: boolean;
    onSelect: (sid: string) => void;
  }

  // Avoid: bloated interface with optional props
  ```

- **D - Dependency Inversion**: Components depend on abstractions

  ```tsx
  // Good: component receives data via props/hooks
  function SlideList({ slides, onSelect }: Props) { ... }

  // Avoid: component directly imports global state
  ```

### YAGNI (You Aren't Gonna Need It)

- Don't add props "just in case"
- Start with inline styles, extract to components when reused
- Avoid premature optimization (memo, useMemo, useCallback)

### KISS (Keep It Simple, Stupid)

- Prefer composition over configuration
- Use native HTML elements when possible
- Minimize state - derive values when possible

### DRY (Don't Repeat Yourself)

- Avoid duplicating code
- Use functions, classes, and modules to DRY code
- Use patterns and templates to DRY code

## Code Organization

```
src/
├── main.tsx           # App entry point
├── App.tsx            # Root component, routing setup
├── api/               # API layer - HTTP requests only
│   ├── index.ts       # Axios/fetch instance, interceptors
│   ├── slides.ts      # Slides API functions
│   ├── images.ts      # Images API functions
│   └── style.ts       # Style API functions
├── stores/            # Zustand stores - global state only
│   ├── index.ts       # Store exports
│   ├── slideStore.ts  # Slides & project state
│   └── playerStore.ts # Playback state
├── components/        # UI components
│   ├── layout/        # Layout components (Header, Sidebar, etc.)
│   ├── slides/        # Slide-related components
│   ├── preview/       # Image preview components
│   ├── player/        # Fullscreen player
│   ├── style/         # Style picker modal
│   └── common/        # Reusable UI primitives
├── hooks/             # Custom React hooks
├── types/             # TypeScript type definitions
└── styles/            # Global styles
```

### Component Structure

```tsx
// components/slides/SlideItem.tsx

// 1. Imports (React, libraries, local)
import { useState, useCallback } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Slide } from '@/types';

// 2. Types
interface SlideItemProps {
  slide: Slide;
  isSelected: boolean;
  onSelect: (sid: string) => void;
  onEdit: (sid: string, content: string) => void;
}

// 3. Component
export function SlideItem({ slide, isSelected, onSelect, onEdit }: SlideItemProps) {
  // 3a. Hooks
  const [isEditing, setIsEditing] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: slide.sid,
  });

  // 3b. Derived state
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // 3c. Handlers
  const handleDoubleClick = useCallback(() => {
    setIsEditing(true);
  }, []);

  // 3d. Render
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onSelect(slide.sid)}
      onDoubleClick={handleDoubleClick}
      className={`p-4 rounded-lg ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
    >
      {isEditing ? (
        <SlideEditor ... />
      ) : (
        <p>{slide.content}</p>
      )}
    </div>
  );
}
```

## State Management (Zustand)

### Store Structure

```typescript
// stores/slideStore.ts
import { create } from 'zustand';
import { slidesApi } from '@/api/slides';
import type { Slide, Style, ProjectResponse } from '@/types';

interface SlideState {
  // Data
  slug: string | null;
  title: string;
  style: Style | null;
  slides: Slide[];
  selectedSlideId: string | null;

  // Loading states
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;

  // Actions
  loadProject: (slug: string) => Promise<void>;
  selectSlide: (sid: string) => void;
  createSlide: (content: string, position?: number) => Promise<void>;
  updateSlide: (sid: string, content: string) => Promise<void>;
  deleteSlide: (sid: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;
  clearError: () => void;
}

export const useSlideStore = create<SlideState>((set, get) => ({
  // Initial state
  slug: null,
  title: '',
  style: null,
  slides: [],
  selectedSlideId: null,
  isLoading: false,
  isGenerating: false,
  error: null,

  // Actions
  loadProject: async (slug) => {
    set({ isLoading: true, error: null });
    try {
      const data = await slidesApi.getProject(slug);
      set({
        slug,
        title: data.title,
        style: data.style,
        slides: data.slides,
        selectedSlideId: data.slides[0]?.sid ?? null,
        isLoading: false,
      });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  selectSlide: (sid) => set({ selectedSlideId: sid }),

  // ... other actions
}));
```

### Store Best Practices

```typescript
// DO: Keep stores focused
const useSlideStore = create<SlideState>(...);  // Slide data
const usePlayerStore = create<PlayerState>(...);  // Playback state

// DON'T: Create god stores with everything
const useAppStore = create<EverythingState>(...);

// DO: Use selectors for derived state
const selectedSlide = useSlideStore(
  (state) => state.slides.find(s => s.sid === state.selectedSlideId)
);

// DON'T: Store derived state
const useSlideStore = create((set) => ({
  slides: [],
  selectedSlideId: null,
  selectedSlide: null,  // This is derived, don't store it!
}));
```

## Concurrency & Async

### API Request Patterns

```typescript
// api/index.ts
const BASE_URL = '/api';

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

// api/slides.ts
export const slidesApi = {
  getProject: (slug: string) =>
    request<ProjectResponse>(`/slides/${slug}`),

  createSlide: (slug: string, data: CreateSlideRequest) =>
    request<SlideResponse>(`/slides/${slug}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
```

### Loading States

```tsx
function SlideList() {
  const { slides, isLoading, error } = useSlideStore();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (slides.length === 0) {
    return <EmptyState message="No slides yet" />;
  }

  return (
    <div>
      {slides.map(slide => <SlideItem key={slide.sid} slide={slide} />)}
    </div>
  );
}
```

### Optimistic Updates

```typescript
// For better UX, update UI before server confirms
reorderSlides: async (slideIds) => {
  const prevSlides = get().slides;

  // Optimistic update
  const reorderedSlides = slideIds.map(
    id => prevSlides.find(s => s.sid === id)!
  );
  set({ slides: reorderedSlides });

  try {
    await slidesApi.reorderSlides(get().slug!, slideIds);
  } catch (e) {
    // Rollback on error
    set({ slides: prevSlides, error: (e as Error).message });
  }
},
```

### Debouncing

```typescript
// hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage in SlideEditor
function SlideEditor({ slide, onSave }: Props) {
  const [content, setContent] = useState(slide.content);
  const debouncedContent = useDebounce(content, 500);

  useEffect(() => {
    if (debouncedContent !== slide.content) {
      onSave(slide.sid, debouncedContent);
    }
  }, [debouncedContent, slide.sid, slide.content, onSave]);

  return <textarea value={content} onChange={e => setContent(e.target.value)} />;
}
```

## Error Handling

### Error Boundary

```tsx
// components/common/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="p-4 text-red-500">
          Something went wrong: {this.state.error?.message}
        </div>
      );
    }
    return this.props.children;
  }
}
```

### API Error Handling

```typescript
// types/index.ts
export interface ApiError {
  detail: string;
  error_code?: string;
}

// api/index.ts
export class ApiRequestError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode?: string
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

// Handle in components
async function handleGenerateImage() {
  try {
    await generateImage(selectedSlideId);
  } catch (e) {
    if (e instanceof ApiRequestError) {
      if (e.statusCode === 502) {
        toast.error('Image generation failed. Please try again.');
      } else if (e.statusCode === 429) {
        toast.error('Rate limited. Please wait a moment.');
      }
    } else {
      toast.error('An unexpected error occurred.');
    }
  }
}
```

### Form Validation

```tsx
function StylePickerForm({ onSubmit }: Props) {
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!prompt.trim()) {
      setError('Please enter a style description');
      return;
    }

    if (prompt.length < 5) {
      setError('Description must be at least 5 characters');
      return;
    }

    onSubmit(prompt);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        className={error ? 'border-red-500' : ''}
      />
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button type="submit">Generate</button>
    </form>
  );
}
```

## Logging & Debugging

### Console Logging (Development Only)

```typescript
// utils/logger.ts
const isDev = import.meta.env.DEV;

export const logger = {
  debug: (...args: unknown[]) => {
    if (isDev) console.debug('[DEBUG]', ...args);
  },
  info: (...args: unknown[]) => {
    if (isDev) console.info('[INFO]', ...args);
  },
  warn: (...args: unknown[]) => {
    console.warn('[WARN]', ...args);
  },
  error: (...args: unknown[]) => {
    console.error('[ERROR]', ...args);
  },
};

// Usage
logger.debug('Slide selected:', sid);
logger.info('Project loaded:', { slug, slideCount: slides.length });
logger.error('API request failed:', error);
```

### React DevTools Integration

```typescript
// stores/slideStore.ts
import { devtools } from 'zustand/middleware';

export const useSlideStore = create<SlideState>()(
  devtools(
    (set, get) => ({
      // ... store implementation
    }),
    { name: 'SlideStore' }  // Shows in Redux DevTools
  )
);
```

## Testing

### Test Structure

```
src/
├── __tests__/
│   ├── components/
│   │   └── SlideItem.test.tsx
│   ├── stores/
│   │   └── slideStore.test.ts
│   └── hooks/
│       └── useKeyboard.test.ts
```

### Component Testing

```tsx
// __tests__/components/SlideItem.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SlideItem } from '@/components/slides/SlideItem';

describe('SlideItem', () => {
  const mockSlide = {
    sid: 'slide_001',
    content: 'Test slide content',
    content_hash: 'abc123',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('renders slide content', () => {
    render(
      <SlideItem
        slide={mockSlide}
        isSelected={false}
        onSelect={vi.fn()}
        onEdit={vi.fn()}
      />
    );
    expect(screen.getByText('Test slide content')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn();
    render(
      <SlideItem
        slide={mockSlide}
        isSelected={false}
        onSelect={onSelect}
        onEdit={vi.fn()}
      />
    );
    fireEvent.click(screen.getByText('Test slide content'));
    expect(onSelect).toHaveBeenCalledWith('slide_001');
  });
});
```

### Running Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

## Code Style

### TypeScript Strict Mode

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true
  }
}
```

### Naming Conventions

| Type             | Convention                    | Example                   |
|------------------|-------------------------------|---------------------------|
| Components       | PascalCase                    | `SlideItem.tsx`           |
| Hooks            | camelCase with `use` prefix   | `useSlides.ts`            |
| Stores           | camelCase with `Store` suffix | `slideStore.ts`           |
| Types/Interfaces | PascalCase                    | `Slide`, `SlideItemProps` |
| Constants        | SCREAMING_SNAKE_CASE          | `API_BASE_URL`            |
| CSS Classes      | kebab-case (Tailwind)         | `bg-blue-500`             |

### Import Order

```tsx
// 1. React
import { useState, useEffect } from 'react';

// 2. Third-party libraries
import { useSortable } from '@dnd-kit/sortable';

// 3. Internal modules (absolute imports)
import { useSlideStore } from '@/stores';
import type { Slide } from '@/types';

// 4. Relative imports
import { SlideEditor } from './SlideEditor';

// 5. Styles
import './SlideItem.css';
```

### Tailwind Best Practices

```tsx
// DO: Use Tailwind utilities directly
<button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
  Click me
</button>

// DO: Extract repeated patterns to components
function Button({ children, variant = 'primary' }: ButtonProps) {
  const variants = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  };
  return (
    <button className={`px-4 py-2 rounded ${variants[variant]}`}>
      {children}
    </button>
  );
}

// AVOID: Using @apply excessively in CSS
```
