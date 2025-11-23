//! 网络管理器模块
//!
//! 整合 WebSocket 连接、状态管理和消息处理

use super::{
    client::{ClientError, ScribeClient, WsSink, WsStream},
    protocol::{ClientMessage, ServerMessage},
    state_machine::{ConnectionState, StateMachine},
};
use futures_util::{SinkExt, StreamExt};
use std::sync::Arc;
use thiserror::Error;
use tokio::sync::{RwLock, mpsc};
use tokio_tungstenite::tungstenite::Message;
use tracing::{debug, error, info, warn};

#[derive(Error, Debug)]
pub enum ManagerError {
    #[error("Client error: {0}")]
    Client(#[from] ClientError),

    #[error("Not connected")]
    NotConnected,

    #[error("Send error: {0}")]
    SendError(String),

    #[error("Already running")]
    AlreadyRunning,
}

type Result<T> = std::result::Result<T, ManagerError>;

/// 网络管理器
///
/// 负责管理 WebSocket 连接生命周期、发送音频数据、接收转写结果
pub struct NetworkManager {
    client: ScribeClient,
    state: Arc<RwLock<StateMachine>>,
    audio_rx: mpsc::Receiver<Vec<i16>>,
    event_tx: mpsc::Sender<ServerMessage>,
}

impl NetworkManager {
    /// 创建新的网络管理器
    ///
    /// # Arguments
    /// * `api_key` - ElevenLabs API Key
    /// * `audio_rx` - 接收音频数据的通道
    /// * `event_tx` - 发送服务器事件的通道
    pub fn new(
        api_key: String,
        audio_rx: mpsc::Receiver<Vec<i16>>,
        event_tx: mpsc::Sender<ServerMessage>,
    ) -> Self {
        Self {
            client: ScribeClient::new(api_key),
            state: Arc::new(RwLock::new(StateMachine::default())),
            audio_rx,
            event_tx,
        }
    }

    /// 启动网络管理器
    ///
    /// 建立连接并启动发送/接收任务
    pub async fn run(&mut self) -> Result<()> {
        loop {
            // 1. 检查状态并决定是否连接
            {
                let mut state = self.state.write().await;
                if let Err(e) = state.transition_to_connecting() {
                    error!("Failed to transition to connecting: {}", e);
                    break;
                }
            }

            // 2. 建立连接
            let (ws_sink, ws_stream) = match self.client.connect().await {
                Ok(conn) => conn,
                Err(e) => {
                    error!("Connection failed: {}", e);
                    self.state.write().await.transition_to_error(e.to_string());

                    // 检查是否应该重试
                    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                    if self.state.read().await.should_retry() {
                        continue;
                    } else {
                        break;
                    }
                }
            };

            // 3. 启动发送和接收任务
            let send_handle = self.spawn_send_task(ws_sink);
            let recv_handle = self.spawn_recv_task(ws_stream);

            // 4. 等待任一任务结束
            tokio::select! {
                _ = send_handle => {
                    info!("Send task ended");
                }
                _ = recv_handle => {
                    info!("Recv task ended");
                }
            }

            // 5. 决定是否重连
            let should_retry = self.state.read().await.should_retry();
            if !should_retry {
                info!("Not retrying, stopping network manager");
                break;
            }
        }

        Ok(())
    }

    /// 生成发送任务
    fn spawn_send_task(&mut self, mut ws_sink: WsSink) -> tokio::task::JoinHandle<()> {
        let mut audio_rx = std::mem::replace(
            &mut self.audio_rx,
            mpsc::channel(1).1, // 创建一个虚拟接收器
        );

        tokio::spawn(async move {
            info!("Send task started");

            let mut buffer = Vec::new();
            let mut last_send = tokio::time::Instant::now();
            let mut last_audio_received = tokio::time::Instant::now();
            let mut committed = false; // 是否已发送 commit

            const BATCH_INTERVAL_MS: u64 = 500; // 累积 500ms 再发送
            const SILENCE_COMMIT_MS: u64 = 2000; // 静音 2 秒后自动 commit

            loop {
                tokio::select! {
                    // 接收音频数据
                    Some(audio_chunk) = audio_rx.recv() => {
                        buffer.extend_from_slice(&audio_chunk);
                        last_audio_received = tokio::time::Instant::now();
                        committed = false; // 收到新音频，重置 commit 状态
                    }

                    // 定时发送
                    _ = tokio::time::sleep_until(last_send + tokio::time::Duration::from_millis(BATCH_INTERVAL_MS)) => {
                        if !buffer.is_empty() {
                            // 创建消息
                            let msg = ClientMessage::audio_chunk(&buffer);

                            // 序列化为 JSON
                            let json = match msg.to_json() {
                                Ok(j) => j,
                                Err(e) => {
                                    error!("Failed to serialize message: {}", e);
                                    buffer.clear();
                                    last_send = tokio::time::Instant::now();
                                    continue;
                                }
                            };

                            // 发送
                            if let Err(e) = ws_sink.send(Message::Text(json.into())).await {
                                error!("Failed to send audio: {}", e);
                                break;
                            }

                            debug!("Sent batched audio: {} samples (~{}ms)",
                                buffer.len(),
                                (buffer.len() as f64 / 16000.0 * 1000.0) as u64
                            );

                            buffer.clear();
                            last_send = tokio::time::Instant::now();
                        } else {
                            // 缓冲区为空，检查是否需要发送 commit
                            let silence_duration = last_audio_received.elapsed();
                            if !committed && silence_duration.as_millis() >= SILENCE_COMMIT_MS as u128 {
                                info!("Silence detected for {}ms, sending commit signal", silence_duration.as_millis());

                                let commit_msg = ClientMessage::commit();
                                if let Ok(json) = commit_msg.to_json() {
                                    if let Err(e) = ws_sink.send(Message::Text(json.into())).await {
                                        error!("Failed to send commit: {}", e);
                                        break;
                                    }
                                    committed = true;
                                }
                            }

                            last_send = tokio::time::Instant::now();
                        }
                    }
                }
            }

            info!("Send task stopped");
        })
    }

    /// 生成接收任务
    fn spawn_recv_task(&self, mut ws_stream: WsStream) -> tokio::task::JoinHandle<()> {
        let state = self.state.clone();
        let event_tx = self.event_tx.clone();

        tokio::spawn(async move {
            info!("Recv task started");

            while let Some(msg) = ws_stream.next().await {
                match msg {
                    Ok(Message::Text(text)) => {
                        debug!("Received message: {}", text);

                        // 解析消息
                        match ServerMessage::from_json(&text) {
                            Ok(server_msg) => {
                                // 处理状态更新
                                Self::handle_state_update(&state, &server_msg).await;

                                // 转发事件
                                if event_tx.send(server_msg).await.is_err() {
                                    error!("Event channel closed");
                                    break;
                                }
                            }
                            Err(e) => {
                                error!("Failed to parse server message: {}", e);
                            }
                        }
                    }
                    Ok(Message::Close(frame)) => {
                        info!("WebSocket closed by server: {:?}", frame);
                        break;
                    }
                    Ok(Message::Ping(_)) => {
                        debug!("Received ping");
                    }
                    Ok(Message::Pong(_)) => {
                        debug!("Received pong");
                    }
                    Err(e) => {
                        error!("WebSocket error: {}", e);
                        state.write().await.transition_to_error(e.to_string());
                        break;
                    }
                    _ => {}
                }
            }

            info!("Recv task stopped");
        })
    }

    /// 处理状态更新
    async fn handle_state_update(state: &Arc<RwLock<StateMachine>>, message: &ServerMessage) {
        match message {
            ServerMessage::SessionStarted { session_id, .. } => {
                if let Err(e) = state
                    .write()
                    .await
                    .transition_to_connected(session_id.clone())
                {
                    warn!("Failed to transition to connected: {}", e);
                }
            }
            ServerMessage::InputError { error_message } => {
                state
                    .write()
                    .await
                    .transition_to_error(error_message.clone());
            }
            ServerMessage::AuthError { error } => {
                error!("Authentication error: {}", error);
                state
                    .write()
                    .await
                    .transition_to_error(error.clone());
            }
            ServerMessage::CommitThrottled { error } => {
                // 这是一个警告，不是致命错误，不需要关闭连接
                warn!("Commit throttled: {}", error);
            }
            ServerMessage::SessionEnded { reason } => {
                info!("Session ended: {}", reason);
                state.write().await.transition_to_idle();
            }
            _ => {}
        }
    }

    /// 获取当前连接状态
    pub async fn get_state(&self) -> ConnectionState {
        self.state.read().await.current_state().clone()
    }

    /// 断开连接
    pub async fn disconnect(&self) {
        self.state.write().await.transition_to_disconnecting();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_manager_creation() {
        let (audio_tx, audio_rx) = mpsc::channel(100);
        let (event_tx, _event_rx) = mpsc::channel(100);

        let _manager = NetworkManager::new("test-api-key".to_string(), audio_rx, event_tx);

        drop(audio_tx);
    }

    #[tokio::test]
    async fn test_get_state() {
        let (_audio_tx, audio_rx) = mpsc::channel(100);
        let (event_tx, _event_rx) = mpsc::channel(100);

        let manager = NetworkManager::new("test-key".to_string(), audio_rx, event_tx);

        let state = manager.get_state().await;
        assert_eq!(state.name(), "idle");
    }

    #[tokio::test]
    async fn test_disconnect() {
        let (_audio_tx, audio_rx) = mpsc::channel(100);
        let (event_tx, _event_rx) = mpsc::channel(100);

        let manager = NetworkManager::new("test-key".to_string(), audio_rx, event_tx);
        manager.disconnect().await;

        let state = manager.get_state().await;
        assert_eq!(state.name(), "disconnecting");
    }
}
