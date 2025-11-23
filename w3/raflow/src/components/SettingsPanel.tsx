/**
 * 设置面板组件
 *
 * 配置 API Key、热键、语言等设置
 */

import { invoke } from '@tauri-apps/api/core';
import { useEffect, useState } from 'react';
import { useSettingsStore } from '../store/settings';

interface Config {
  api_key: string;
  hotkey: string;
  language: string;
  keyboard_max_chars: number;
  enable_blacklist: boolean;
}

export function SettingsPanel() {
  const {
    apiKey,
    hotkey,
    language,
    keyboardMaxChars,
    enableBlacklist,
    setApiKey,
    setHotkey,
    setLanguage,
    setKeyboardMaxChars,
    setEnableBlacklist,
  } = useSettingsStore();

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const config = await invoke<Config>('get_config');
      setApiKey(config.api_key);
      setHotkey(config.hotkey);
      setLanguage(config.language);
      setKeyboardMaxChars(config.keyboard_max_chars);
      setEnableBlacklist(config.enable_blacklist);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage('加载设置失败');
    }
  }

  async function saveSettings() {
    setSaving(true);
    setMessage('');

    try {
      await invoke('save_config', {
        config: {
          api_key: apiKey,
          hotkey,
          language,
          keyboard_max_chars: keyboardMaxChars,
          enable_blacklist: enableBlacklist,
        },
      });
      setMessage('设置已保存');
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage('保存失败');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="settings-panel">
      <h1>RAFlow 设置</h1>

      {/* API Key 设置 */}
      <div className="form-group">
        <label htmlFor="api-key">ElevenLabs API Key</label>
        <input
          id="api-key"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="输入你的 API Key"
          className="input"
        />
        <p className="help-text">
          从{' '}
          <a href="https://elevenlabs.io" target="_blank" rel="noopener noreferrer">
            elevenlabs.io
          </a>{' '}
          获取 API Key
        </p>
      </div>

      {/* 热键设置 */}
      <div className="form-group">
        <label htmlFor="hotkey">全局热键</label>
        <input
          id="hotkey"
          type="text"
          value={hotkey}
          onChange={(e) => setHotkey(e.target.value)}
          placeholder="CommandOrControl+Shift+\"
          className="input"
        />
        <p className="help-text">使用 Tauri 热键格式，如 CommandOrControl+Shift+\</p>
      </div>

      {/* 语言设置 */}
      <div className="form-group">
        <label htmlFor="language">识别语言</label>
        <select
          id="language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="select"
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
          <option value="es">Español</option>
        </select>
      </div>

      {/* 高级设置 */}
      <details className="advanced-settings">
        <summary>高级设置</summary>

        <div className="form-group">
          <label htmlFor="keyboard-max">键盘输入最大字符数</label>
          <input
            id="keyboard-max"
            type="number"
            value={keyboardMaxChars}
            onChange={(e) => setKeyboardMaxChars(Number(e.target.value))}
            min={1}
            max={100}
            className="input"
          />
          <p className="help-text">
            超过此长度的文本将使用剪贴板策略（推荐 10）
          </p>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={enableBlacklist}
              onChange={(e) => setEnableBlacklist(e.target.checked)}
            />
            <span>启用黑名单保护</span>
          </label>
          <p className="help-text">
            阻止在密码管理器等敏感应用中自动输入
          </p>
        </div>
      </details>

      {/* 保存按钮 */}
      <div className="actions">
        <button
          onClick={saveSettings}
          disabled={saving || !apiKey}
          className="button-primary"
        >
          {saving ? '保存中...' : '保存设置'}
        </button>

        {message && (
          <div className={`message ${message.includes('失败') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}
      </div>

      {/* 版本信息 */}
      <div className="version-info">
        <p>RAFlow v0.1.0</p>
        <p>
          <a
            href="https://github.com/raflow/raflow"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>{' '}
          |{' '}
          <a
            href="https://github.com/raflow/raflow/issues"
            target="_blank"
            rel="noopener noreferrer"
          >
            反馈问题
          </a>
        </p>
      </div>
    </div>
  );
}
