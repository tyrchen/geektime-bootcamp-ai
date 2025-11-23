/**
 * 转写状态管理
 *
 * 使用 Zustand 管理实时转写文本和连接状态
 */

import { create } from 'zustand';

type ConnectionState = 'idle' | 'connecting' | 'listening' | 'error';

interface TranscriptState {
  // 转写文本
  partial: string;
  committed: string[];

  // UI 状态
  isRecording: boolean;
  audioLevel: number; // 0-100

  // 连接状态
  connectionState: ConnectionState;
  errorMessage?: string;

  // Actions
  setPartial: (text: string) => void;
  addCommitted: (text: string) => void;
  setConnectionState: (state: ConnectionState) => void;
  setAudioLevel: (level: number) => void;
  setError: (message: string) => void;
  clear: () => void;
}

export const useTranscriptStore = create<TranscriptState>((set) => ({
  // 初始状态
  partial: '',
  committed: [],
  isRecording: false,
  audioLevel: 0,
  connectionState: 'idle',

  // 设置部分转写
  setPartial: (text) => set({ partial: text }),

  // 添加已确认的转写
  addCommitted: (text) =>
    set((state) => ({
      committed: [...state.committed, text],
      partial: '',
    })),

  // 设置连接状态
  setConnectionState: (connectionState) => set({ connectionState }),

  // 设置音量级别
  setAudioLevel: (audioLevel) => set({ audioLevel, isRecording: audioLevel > 0 }),

  // 设置错误
  setError: (errorMessage) =>
    set({ errorMessage, connectionState: 'error' }),

  // 清空所有状态
  clear: () =>
    set({
      partial: '',
      committed: [],
      audioLevel: 0,
      isRecording: false,
      errorMessage: undefined,
    }),
}));
