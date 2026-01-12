import { useEffect, useState, useRef } from 'react';
import { useSlideStore } from '@/stores';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MainContent } from '@/components/layout/MainContent';
import { StylePickerModal } from '@/components/style/StylePickerModal';
import { FullscreenPlayer } from '@/components/player/FullscreenPlayer';

function App() {
  const { loadProject, createProject, style, isLoading, error } = useSlideStore();
  const [showStylePicker, setShowStylePicker] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [projectLoaded, setProjectLoaded] = useState(false);
  const hasCheckedStyle = useRef(false);

  // Get slug from URL path: /slug-name
  const slug = getSlugFromUrl();

  // Load project on mount if slug exists
  useEffect(() => {
    if (slug) {
      setProjectLoaded(false);
      hasCheckedStyle.current = false;
      loadProject(slug).then(() => {
        setProjectLoaded(true);
      });
    }
  }, [slug, loadProject]);

  // Only auto-show style picker once after project has loaded if no style is set
  useEffect(() => {
    if (projectLoaded && !hasCheckedStyle.current) {
      hasCheckedStyle.current = true;
      if (style === null) {
        setShowStylePicker(true);
      }
    }
  }, [projectLoaded, style]);

  const handleOpenStylePicker = () => {
    setShowStylePicker(true);
  };

  const handleCloseStylePicker = () => {
    setShowStylePicker(false);
  };

  if (isLoading) {
    return (
      <div
        className="h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--md-cream)' }}
      >
        <div className="text-center">
          <div
            className="animate-spin w-12 h-12 border-4 border-t-transparent rounded-full mx-auto mb-4"
            style={{ borderColor: 'var(--md-sky)', borderTopColor: 'transparent' }}
          />
          <p style={{ color: 'var(--md-slate)' }}>Loading project...</p>
        </div>
      </div>
    );
  }

  // Welcome screen when no slug in URL
  if (!slug) {
    const handleCreateProject = async (e: React.FormEvent) => {
      e.preventDefault();
      const projectSlug = newProjectName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
      if (projectSlug) {
        await createProject(projectSlug, newProjectName || projectSlug);
        window.location.href = `/${projectSlug}`;
      }
    };

    return (
      <div
        className="h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--md-cream)' }}
      >
        <div className="text-center max-w-md mx-auto p-8">
          <div
            className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6"
            style={{ backgroundColor: 'var(--md-soft-blue)' }}
          >
            <svg
              className="w-10 h-10"
              style={{ color: 'var(--md-sky-strong)' }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h1
            className="text-3xl font-bold mb-2"
            style={{ color: 'var(--md-ink)' }}
          >
            GenSlides
          </h1>
          <p className="mb-8" style={{ color: 'var(--md-slate)' }}>
            Create AI-powered image slideshows
          </p>
          <form onSubmit={handleCreateProject} className="space-y-4">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="Enter project name..."
              className="md-input"
              autoFocus
            />
            <button
              type="submit"
              disabled={!newProjectName.trim()}
              className="md-btn w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create Project
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--md-cream)' }}
      >
        <div className="text-center max-w-md mx-auto p-6">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: 'var(--md-watermelon)', opacity: 0.2 }}
          >
            <svg
              className="w-8 h-8"
              style={{ color: 'var(--md-watermelon)' }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2
            className="text-xl font-semibold mb-2"
            style={{ color: 'var(--md-ink)' }}
          >
            Failed to load project
          </h2>
          <p className="mb-4" style={{ color: 'var(--md-slate)' }}>{error}</p>
          <button
            onClick={() => window.location.href = '/'}
            className="md-btn"
          >
            Create New Project
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header onOpenStylePicker={handleOpenStylePicker} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <MainContent />
      </div>

      <StylePickerModal
        isOpen={showStylePicker}
        onClose={handleCloseStylePicker}
      />

      <FullscreenPlayer />
    </div>
  );
}

function getSlugFromUrl(): string | null {
  // Get slug from URL path: /slug-name (first path segment)
  const pathname = window.location.pathname;
  const segments = pathname.split('/').filter(Boolean);

  // Return the first segment as the slug, or null if empty
  return segments[0] || null;
}

export default App;
