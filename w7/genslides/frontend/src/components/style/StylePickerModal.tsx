import { useState, useCallback, useEffect } from 'react';
import { useSlideStore } from '@/stores';
import { Modal } from '@/components/common/Modal';
import { Textarea } from '@/components/common/Input';
import { Button } from '@/components/common/Button';

interface StylePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function StylePickerModal({ isOpen, onClose }: StylePickerModalProps) {
  const {
    slug,
    style,
    stylePrompt,
    styleCandidates,
    isGeneratingStyle,
    isSaving,
    setStylePrompt,
    generateStyleCandidates,
    selectStyle,
    clearStyleCandidates,
  } = useSlideStore();

  const [localPrompt, setLocalPrompt] = useState(stylePrompt);

  // Initialize localPrompt with existing style prompt when modal opens
  useEffect(() => {
    if (isOpen) {
      setLocalPrompt(style?.prompt || stylePrompt || '');
    }
  }, [isOpen, style?.prompt, stylePrompt]);

  const handleGenerateCandidates = useCallback(async () => {
    if (localPrompt.trim()) {
      setStylePrompt(localPrompt.trim());
      await generateStyleCandidates(localPrompt.trim());
    }
  }, [localPrompt, setStylePrompt, generateStyleCandidates]);

  const handleSelectStyle = useCallback(
    async (candidateFilename: string) => {
      await selectStyle(candidateFilename);
      onClose();
    },
    [selectStyle, onClose]
  );

  const handleClose = useCallback(() => {
    clearStyleCandidates();
    setLocalPrompt('');
    onClose();
  }, [clearStyleCandidates, onClose]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleGenerateCandidates();
      }
    },
    [handleGenerateCandidates]
  );

  const getStyleImageUrl = (filename: string) => {
    return `/api/slides/${slug}/style/${filename}`;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Choose Presentation Style"
      size="xl"
    >
      <div className="space-y-6">
        {/* Current Style */}
        {style && (
          <div
            className="p-4 rounded-lg"
            style={{
              backgroundColor: 'var(--md-soft-blue)',
              border: '2px solid var(--md-sky)',
            }}
          >
            <div className="flex gap-4">
              <img
                src={getStyleImageUrl(style.image)}
                alt="Current style"
                className="w-24 h-24 object-cover rounded"
                style={{ border: '2px solid var(--md-graphite)' }}
              />
              <div className="flex-1">
                <h4
                  className="font-bold mb-1"
                  style={{ color: 'var(--md-ink)', fontSize: 'var(--font-body)' }}
                >
                  Current Style
                </h4>
                <p
                  style={{ color: 'var(--md-slate)', fontSize: 'var(--font-small)' }}
                >
                  {style.prompt}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Prompt Input */}
        <div>
          <Textarea
            label={style ? "Update Style Description" : "Style Description"}
            value={localPrompt}
            onChange={(e) => setLocalPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the visual style you want (e.g., watercolor painting, soft tones, minimalist design)"
            rows={3}
          />
          <p className="mt-1 text-xs text-surface-400">
            This style will be applied to all generated images in your presentation.
          </p>
        </div>

        {/* Generate Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleGenerateCandidates}
            isLoading={isGeneratingStyle}
            disabled={!localPrompt.trim()}
            className="gap-2"
          >
            <svg
              className="w-5 h-5"
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
            {isGeneratingStyle ? 'Generating Style...' : 'Generate Style Candidates'}
          </Button>
        </div>

        {/* Style Candidates */}
        {styleCandidates.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-surface-700">
              Choose a style:
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {styleCandidates.map((candidate, index) => (
                <div
                  key={candidate.filename}
                  className="group relative rounded-lg overflow-hidden border border-surface-200 hover:border-primary-400 transition-all"
                >
                  <img
                    src={getStyleImageUrl(candidate.filename)}
                    alt={`Style candidate ${index + 1}`}
                    className="w-full aspect-square object-cover"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                    <Button
                      onClick={() => handleSelectStyle(candidate.filename)}
                      isLoading={isSaving}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Select This Style
                    </Button>
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
                    <span className="text-white text-sm font-medium">
                      Option {index + 1}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty state info */}
        {styleCandidates.length === 0 && !isGeneratingStyle && (
          <div className="text-center py-8 text-surface-400">
            <svg
              className="w-12 h-12 mx-auto mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
              />
            </svg>
            <p className="text-sm">
              Enter a style description and generate candidates to choose from.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}
