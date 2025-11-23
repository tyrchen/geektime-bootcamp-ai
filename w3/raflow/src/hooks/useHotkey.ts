/**
 * 热键事件 Hook
 *
 * 监听热键事件并自动切换录音状态
 */

import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';

export function useHotkey() {
  useEffect(() => {
    // 监听热键切换事件
    const unlisten = listen('hotkey_toggle', async () => {
      console.log('Hotkey toggled, calling toggle_recording');

      try {
        await invoke('toggle_recording');
      } catch (error) {
        console.error('Failed to toggle recording:', error);
      }
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);
}
