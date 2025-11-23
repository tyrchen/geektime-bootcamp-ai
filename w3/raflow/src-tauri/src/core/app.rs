//! 应用主控制器
//!
//! 整合音频、网络、输入等所有模块，实现完整的录音-转写-注入流程

use crate::audio::AudioManager;
use crate::config::AppConfig;
use crate::input::{InjectionConfig, TextInjector};
use crate::network::{NetworkManager, ServerMessage};
use crate::system::WindowTracker;
use tauri::{AppHandle, Emitter, Manager};
use thiserror::Error;
use tokio::sync::mpsc;
use tracing::{debug, error, info, warn};

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Audio error: {0}")]
    Audio(String),

    #[error("Network error: {0}")]
    Network(String),

    #[error("Input error: {0}")]
    Input(String),

    #[error("Not configured: {0}")]
    NotConfigured(String),

    #[error("Already running")]
    AlreadyRunning,
}

type Result<T> = std::result::Result<T, AppError>;

/// 应用控制器
///
/// 管理整个应用的生命周期和数据流
/// 拥有 AudioManager 和 NetworkManager 的所有权
pub struct AppController {
    app: AppHandle,
    config: AppConfig,
    audio_manager: Option<AudioManager>,
    stop_tx: Option<mpsc::Sender<()>>,
}

impl AppController {
    /// 创建新的应用控制器
    pub fn new(app: AppHandle, config: AppConfig) -> Self {
        Self {
            app,
            config,
            audio_manager: None,
            stop_tx: None,
        }
    }

    /// 启动录音流程
    ///
    /// 完整流程：
    /// 1. 启动音频采集
    /// 2. 建立 WebSocket 连接
    /// 3. 音频流 -> 重采样 -> 网络发送
    /// 4. 接收转写结果 -> 注入文本
    pub async fn start_recording(&mut self) -> Result<()> {
        // 检查是否已在运行
        if self.audio_manager.is_some() {
            return Err(AppError::AlreadyRunning);
        }

        info!("Starting recording flow");

        // 检查 API Key
        if self.config.api_key.is_empty() {
            return Err(AppError::NotConfigured("API Key not set".to_string()));
        }

        // 创建停止信号通道
        let (stop_tx, mut stop_rx) = mpsc::channel::<()>(1);
        self.stop_tx = Some(stop_tx);

        // 创建通道
        let (audio_tx, audio_rx) = mpsc::channel::<Vec<i16>>(100);
        let (event_tx, mut event_rx) = mpsc::channel::<ServerMessage>(100);

        // 启动音频管理器
        let mut audio_manager =
            AudioManager::new(audio_tx).map_err(|e| AppError::Audio(e.to_string()))?;

        audio_manager
            .start()
            .map_err(|e| AppError::Audio(e.to_string()))?;

        info!("Audio manager started");

        // 保存 audio_manager（拥有所有权）
        self.audio_manager = Some(audio_manager);

        // 启动网络管理器
        let mut network_manager =
            NetworkManager::new(self.config.api_key.clone(), audio_rx, event_tx);

        tokio::spawn(async move {
            if let Err(e) = network_manager.run().await {
                error!("Network manager error: {}", e);
            }
        });

        info!("Network manager started");

        // 启动事件处理任务
        let app_clone = self.app.clone();
        let config_clone = self.config.clone();

        tokio::spawn(async move {
            tokio::select! {
                _ = Self::handle_events(app_clone, config_clone, &mut event_rx) => {
                    info!("Event handler finished");
                }
                _ = stop_rx.recv() => {
                    info!("Stop signal received");
                }
            }
        });

        info!("Event handler started");

        Ok(())
    }

    /// 停止录音流程
    pub async fn stop_recording(&mut self) -> Result<()> {
        info!("Stopping recording flow");

        // 停止音频采集
        if let Some(mut audio_manager) = self.audio_manager.take() {
            audio_manager.stop();
            info!("Audio manager stopped");
        }

        // 发送停止信号
        if let Some(stop_tx) = self.stop_tx.take() {
            let _ = stop_tx.send(()).await;
        }

        // 发送停止事件
        self.app
            .emit("recording_stopped", ())
            .map_err(|e| AppError::Network(e.to_string()))?;

        info!("Recording stopped");

        Ok(())
    }

    /// 检查是否正在运行
    pub fn is_running(&self) -> bool {
        self.audio_manager.is_some()
    }

    /// 处理服务器事件
    async fn handle_events(
        app: AppHandle,
        config: AppConfig,
        event_rx: &mut mpsc::Receiver<ServerMessage>,
    ) {
        info!("Event handler started");

        while let Some(message) = event_rx.recv().await {
            debug!("Received server message: {:?}", message);

            match message {
                ServerMessage::PartialTranscript { text, .. } => {
                    // 发送部分转写到前端
                    if let Err(e) = app.emit(
                        "transcript_update",
                        serde_json::json!({
                            "text": text,
                            "is_final": false,
                        }),
                    ) {
                        warn!("Failed to emit partial transcript: {}", e);
                    }
                }

                ServerMessage::CommittedTranscript { text, confidence } => {
                    info!(
                        "Committed transcript: {} (confidence: {:?})",
                        text, confidence
                    );

                    // 发送最终转写到前端
                    if let Err(e) = app.emit(
                        "transcript_update",
                        serde_json::json!({
                            "text": text,
                            "is_final": true,
                            "confidence": confidence.unwrap_or(1.0),
                        }),
                    ) {
                        warn!("Failed to emit committed transcript: {}", e);
                    }

                    // 执行文本注入
                    let app_for_injection = app.clone();
                    let text_for_injection = text.clone();

                    // 先隐藏 overlay（在异步任务外）
                    if let Some(overlay) = app.get_webview_window("overlay") {
                        if let Err(e) = overlay.hide() {
                            error!("Failed to hide overlay: {}", e);
                        } else {
                            debug!("Overlay hidden before window detection");
                        }
                    }

                    tokio::task::spawn_blocking(move || {
                        // 等待焦点切换完成
                        std::thread::sleep(std::time::Duration::from_millis(300));

                        // 现在获取当前窗口（应该是目标窗口了）
                        let window = match WindowTracker::get_current_window() {
                            Ok(w) => w,
                            Err(e) => {
                                error!("Failed to get current window: {}", e);
                                return;
                            }
                        };

                        // 创建注入配置
                        let injection_config = InjectionConfig {
                            keyboard_max_chars: config.keyboard_max_chars,
                            enable_blacklist: config.enable_blacklist,
                            ..Default::default()
                        };

                        // 创建注入器并注入
                        let mut injector = match TextInjector::with_config(
                            app_for_injection.clone(),
                            injection_config,
                        ) {
                            Ok(i) => i,
                            Err(e) => {
                                error!("Failed to create injector: {}", e);
                                return;
                            }
                        };

                        // 执行注入
                        let runtime = tokio::runtime::Handle::current();
                        if let Err(e) = runtime
                            .block_on(async { injector.inject(&text_for_injection, &window).await })
                        {
                            error!("Injection failed: {}", e);
                        } else {
                            info!("Text injected successfully");
                        }
                    });
                }

                ServerMessage::SessionStarted { session_id, .. } => {
                    info!("Session started: {}", session_id);
                    if let Err(e) = app.emit("session_started", session_id) {
                        warn!("Failed to emit session_started: {}", e);
                    }
                }

                ServerMessage::InputError { error_message } => {
                    error!("Input error from server: {}", error_message);
                    if let Err(e) = app.emit("api_error", error_message) {
                        warn!("Failed to emit api_error: {}", e);
                    }
                }

                ServerMessage::AuthError { error } => {
                    error!("Authentication error: {}", error);
                    if let Err(e) = app.emit("auth_error", error) {
                        warn!("Failed to emit auth_error: {}", e);
                    }
                    break; // 认证失败，停止处理
                }

                ServerMessage::CommitThrottled { error } => {
                    // 提交被限制，这是一个警告，不影响继续运行
                    warn!("Commit throttled by server: {}", error);
                    // 可选：发送到前端供调试
                    if let Err(e) = app.emit("commit_throttled", error) {
                        warn!("Failed to emit commit_throttled: {}", e);
                    }
                }

                ServerMessage::SessionEnded { reason } => {
                    info!("Session ended: {}", reason);
                    if let Err(e) = app.emit("session_ended", reason) {
                        warn!("Failed to emit session_ended: {}", e);
                    }
                    break;
                }
            }
        }

        info!("Event handler stopped");
    }
}

#[cfg(test)]
mod tests {
    // AppController 的完整测试需要 Tauri 运行时
    // 应该在集成测试或 E2E 测试中进行
}
