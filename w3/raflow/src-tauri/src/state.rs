//! 应用全局状态
//!
//! 使用 channel 模式管理应用状态，避免锁竞争

use crate::config::AppConfig;
use tokio::sync::{mpsc, oneshot, watch};
use tracing::info;

/// 录音状态
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecordingState {
    Idle,
    Recording,
    Processing,
}

/// 控制命令
pub enum ControlCommand {
    /// 开始录音
    Start {
        config: AppConfig,
        response: oneshot::Sender<Result<(), String>>,
    },
    /// 停止录音
    Stop {
        response: oneshot::Sender<Result<(), String>>,
    },
}

/// 应用全局状态
///
/// 使用 channel 模式：
/// - control_tx: 发送控制命令到后台任务
/// - state_rx: 订阅状态变化（只读）
pub struct AppState {
    /// 控制命令发送端
    pub control_tx: mpsc::Sender<ControlCommand>,
    /// 状态接收端（watch channel，可以多个订阅者）
    pub state_rx: watch::Receiver<RecordingState>,
}

impl AppState {
    /// 创建新的应用状态
    ///
    /// 同时启动后台控制任务
    pub fn new() -> (
        Self,
        mpsc::Receiver<ControlCommand>,
        watch::Sender<RecordingState>,
    ) {
        info!("Initializing app state with channel pattern");

        let (control_tx, control_rx) = mpsc::channel::<ControlCommand>(10);
        let (state_tx, state_rx) = watch::channel(RecordingState::Idle);

        let state = Self {
            control_tx,
            state_rx,
        };

        (state, control_rx, state_tx)
    }

    /// 发送开始录音命令
    pub async fn start_recording(&self, config: AppConfig) -> Result<(), String> {
        let (response_tx, response_rx) = oneshot::channel();

        self.control_tx
            .send(ControlCommand::Start {
                config,
                response: response_tx,
            })
            .await
            .map_err(|_| "Control channel closed".to_string())?;

        response_rx
            .await
            .map_err(|_| "Response channel closed".to_string())?
    }

    /// 发送停止录音命令
    pub async fn stop_recording(&self) -> Result<(), String> {
        let (response_tx, response_rx) = oneshot::channel();

        self.control_tx
            .send(ControlCommand::Stop {
                response: response_tx,
            })
            .await
            .map_err(|_| "Control channel closed".to_string())?;

        response_rx
            .await
            .map_err(|_| "Response channel closed".to_string())?
    }

    /// 获取当前状态
    pub fn get_state(&self) -> RecordingState {
        *self.state_rx.borrow()
    }

    /// 订阅状态变化
    pub fn subscribe(&self) -> watch::Receiver<RecordingState> {
        self.state_rx.clone()
    }
}

impl Clone for AppState {
    fn clone(&self) -> Self {
        Self {
            control_tx: self.control_tx.clone(),
            state_rx: self.state_rx.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_app_state_creation() {
        let (state, _control_rx, _state_tx) = AppState::new();
        assert_eq!(state.get_state(), RecordingState::Idle);
    }

    #[tokio::test]
    async fn test_state_subscribe() {
        let (state, _control_rx, state_tx) = AppState::new();

        let mut subscriber = state.subscribe();

        // 更新状态
        state_tx.send(RecordingState::Recording).unwrap();

        // 订阅者应该收到更新
        subscriber.changed().await.unwrap();
        assert_eq!(*subscriber.borrow(), RecordingState::Recording);
    }

    #[tokio::test]
    async fn test_control_command_send() {
        let (state, mut control_rx, _state_tx) = AppState::new();

        // 发送开始命令（在后台任务中）
        tokio::spawn(async move {
            let (tx, _rx) = oneshot::channel();
            let _ = state
                .control_tx
                .send(ControlCommand::Start {
                    config: AppConfig::default(),
                    response: tx,
                })
                .await;
        });

        // 接收命令
        let cmd = control_rx.recv().await;
        assert!(cmd.is_some());
    }
}
