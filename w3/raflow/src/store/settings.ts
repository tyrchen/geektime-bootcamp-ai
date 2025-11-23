/**
 * 设置状态管理
 *
 * 管理应用配置和用户偏好
 */

import { create } from 'zustand';

interface SettingsState {
  // API 配置
  apiKey: string;

  // 热键配置
  hotkey: string;

  // 语言设置
  language: string;

  // UI 偏好
  theme: 'light' | 'dark' | 'auto';
  showWaveform: boolean;

  // 注入配置
  keyboardMaxChars: number;
  enableBlacklist: boolean;

  // Actions
  setApiKey: (key: string) => void;
  setHotkey: (hotkey: string) => void;
  setLanguage: (language: string) => void;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  setShowWaveform: (show: boolean) => void;
  setKeyboardMaxChars: (max: number) => void;
  setEnableBlacklist: (enable: boolean) => void;
  reset: () => void;
}

const DEFAULT_SETTINGS = {
  apiKey: '',
  hotkey: 'CommandOrControl+Shift+\\',
  language: 'zh',
  theme: 'auto' as const,
  showWaveform: true,
  keyboardMaxChars: 10,
  enableBlacklist: true,
};

export const useSettingsStore = create<SettingsState>((set) => ({
  // 初始状态
  ...DEFAULT_SETTINGS,

  // 设置 API Key
  setApiKey: (apiKey) => set({ apiKey }),

  // 设置热键
  setHotkey: (hotkey) => set({ hotkey }),

  // 设置语言
  setLanguage: (language) => set({ language }),

  // 设置主题
  setTheme: (theme) => set({ theme }),

  // 设置波形显示
  setShowWaveform: (showWaveform) => set({ showWaveform }),

  // 设置键盘最大字符数
  setKeyboardMaxChars: (keyboardMaxChars) => set({ keyboardMaxChars }),

  // 设置黑名单启用
  setEnableBlacklist: (enableBlacklist) => set({ enableBlacklist }),

  // 重置为默认值
  reset: () => set(DEFAULT_SETTINGS),
}));
