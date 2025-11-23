/**
 * 悬浮窗组件
 *
 * 显示实时转写文本和音频波形
 */

import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';
import { useTranscriptStore } from '../store/transcript';

interface TranscriptEvent {
  text: string;
  is_final: boolean;
  confidence?: number;
}

interface AudioLevelEvent {
  level: number; // 0-100
}

export function OverlayWindow() {
  const {
    partial,
    committed,
    audioLevel,
    isRecording,
    connectionState,
    setPartial,
    addCommitted,
    setAudioLevel,
  } = useTranscriptStore();

  useEffect(() => {
    // 监听转写事件
    const unlistenTranscript = listen<TranscriptEvent>('transcript_update', (event) => {
      if (event.payload.is_final) {
        addCommitted(event.payload.text);
      } else {
        setPartial(event.payload.text);
      }
    });

    // 监听音量事件
    const unlistenAudio = listen<AudioLevelEvent>('audio_level', (event) => {
      setAudioLevel(event.payload.level);
    });

    return () => {
      unlistenTranscript.then((fn) => fn());
      unlistenAudio.then((fn) => fn());
    };
  }, [addCommitted, setPartial, setAudioLevel]);

  return (
    <div className="overlay-container">
      {/* 状态指示器 */}
      <div className="status-indicator">
        <div className={`dot ${isRecording ? 'recording' : connectionState}`} />
        <span className="status-text">
          {connectionState === 'connecting' && '正在连接...'}
          {connectionState === 'listening' && !isRecording && '等待中'}
          {isRecording && '正在录音...'}
          {connectionState === 'error' && '连接错误'}
        </span>
      </div>

      {/* 文本显示区域 */}
      <div className="transcript-area">
        {/* 已确认的文本 */}
        {committed.map((text, i) => (
          <span key={i} className="committed">
            {text}{' '}
          </span>
        ))}

        {/* 实时文本 */}
        {partial && <span className="partial">{partial}</span>}

        {/* 空状态提示 */}
        {!partial && committed.length === 0 && (
          <span className="placeholder">按住热键开始说话...</span>
        )}
      </div>

      {/* 音量波形 */}
      <div className="waveform">
        <div
          className="level-bar"
          style={{
            width: `${audioLevel}%`,
            transition: 'width 0.1s linear',
          }}
        />
      </div>
    </div>
  );
}
