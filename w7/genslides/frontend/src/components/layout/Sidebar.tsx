import { useSlideStore } from '@/stores';
import { SlideList } from '@/components/slides/SlideList';

export function Sidebar() {
  const { style } = useSlideStore();

  return (
    <aside
      className="w-80 flex flex-col h-full overflow-hidden"
      style={{
        backgroundColor: 'var(--md-fog)',
        borderRight: '2px solid var(--md-graphite)',
      }}
    >
      {/* Style indicator */}
      {style && (
        <div
          className="p-3 shrink-0 flex items-center gap-2"
          style={{
            fontSize: 'var(--font-tiny)',
            color: 'var(--md-slate)',
            borderBottom: '2px solid var(--md-graphite)',
          }}
        >
          <svg
            className="w-4 h-4 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
            />
          </svg>
          <span className="truncate">{style.prompt}</span>
        </div>
      )}

      {/* Slide List */}
      <div className="flex-1 overflow-y-auto">
        <SlideList />
      </div>
    </aside>
  );
}
