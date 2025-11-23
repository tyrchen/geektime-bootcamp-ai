//! WebSocket 连接状态机
//!
//! 管理连接生命周期和状态转换

use std::time::{Duration, Instant};
use thiserror::Error;
use tracing::{debug, info, warn};

#[derive(Error, Debug)]
pub enum StateError {
    #[error("Invalid state transition from {from:?} to {to:?}")]
    InvalidTransition { from: String, to: String },

    #[error("Max retries reached: {0}")]
    MaxRetriesReached(u32),
}

/// 连接状态枚举
#[derive(Debug, Clone, PartialEq)]
pub enum ConnectionState {
    /// 空闲状态
    Idle,

    /// 连接中
    Connecting {
        /// 重试次数
        attempt: u32,
    },

    /// 已连接
    Connected {
        /// 会话 ID
        session_id: String,
        /// 连接建立时间
        connected_at: Instant,
    },

    /// 错误状态
    Error {
        /// 错误消息
        message: String,
        /// 重试时间
        retry_at: Instant,
        /// 已重试次数
        attempt: u32,
    },

    /// 正在断开
    Disconnecting,
}

impl ConnectionState {
    /// 获取状态名称
    pub fn name(&self) -> &str {
        match self {
            ConnectionState::Idle => "idle",
            ConnectionState::Connecting { .. } => "connecting",
            ConnectionState::Connected { .. } => "connected",
            ConnectionState::Error { .. } => "error",
            ConnectionState::Disconnecting => "disconnecting",
        }
    }

    /// 是否已连接
    pub fn is_connected(&self) -> bool {
        matches!(self, ConnectionState::Connected { .. })
    }

    /// 是否可以重试
    pub fn can_retry(&self) -> bool {
        match self {
            ConnectionState::Error { attempt, .. } => *attempt < 3,
            _ => false,
        }
    }
}

/// 连接状态机
pub struct StateMachine {
    state: ConnectionState,
    max_retries: u32,
    retry_delay: Duration,
}

impl StateMachine {
    /// 创建新的状态机
    ///
    /// # Arguments
    /// * `max_retries` - 最大重试次数（默认 3）
    /// * `retry_delay` - 重试延迟（默认 2 秒）
    pub fn new(max_retries: u32, retry_delay: Duration) -> Self {
        Self {
            state: ConnectionState::Idle,
            max_retries,
            retry_delay,
        }
    }

    /// 获取当前状态
    pub fn current_state(&self) -> &ConnectionState {
        &self.state
    }

    /// 转换到连接中状态
    pub fn transition_to_connecting(&mut self) -> Result<(), StateError> {
        match &self.state {
            ConnectionState::Idle => {
                info!("State: Idle -> Connecting (attempt 1)");
                self.state = ConnectionState::Connecting { attempt: 1 };
                Ok(())
            }
            ConnectionState::Error { attempt, .. } if *attempt < self.max_retries => {
                let new_attempt = attempt + 1;
                info!("State: Error -> Connecting (attempt {})", new_attempt);
                self.state = ConnectionState::Connecting {
                    attempt: new_attempt,
                };
                Ok(())
            }
            ConnectionState::Error { attempt, .. } => Err(StateError::MaxRetriesReached(*attempt)),
            _ => {
                warn!("Invalid transition to Connecting from {:?}", self.state);
                Ok(()) // 已经在连接中或已连接，忽略
            }
        }
    }

    /// 转换到已连接状态
    pub fn transition_to_connected(&mut self, session_id: String) -> Result<(), StateError> {
        match &self.state {
            ConnectionState::Connecting { .. } => {
                info!("State: Connecting -> Connected (session: {})", session_id);
                self.state = ConnectionState::Connected {
                    session_id,
                    connected_at: Instant::now(),
                };
                Ok(())
            }
            _ => Err(StateError::InvalidTransition {
                from: self.state.name().to_string(),
                to: "connected".to_string(),
            }),
        }
    }

    /// 转换到错误状态
    pub fn transition_to_error(&mut self, message: String) {
        let attempt = match &self.state {
            ConnectionState::Connecting { attempt } => *attempt,
            ConnectionState::Error { attempt, .. } => *attempt,
            _ => 0,
        };

        warn!(
            "State: {} -> Error (attempt {}, message: {})",
            self.state.name(),
            attempt,
            message
        );

        self.state = ConnectionState::Error {
            message,
            retry_at: Instant::now() + self.retry_delay,
            attempt,
        };
    }

    /// 转换到空闲状态
    pub fn transition_to_idle(&mut self) {
        debug!("State: {} -> Idle", self.state.name());
        self.state = ConnectionState::Idle;
    }

    /// 转换到断开中状态
    pub fn transition_to_disconnecting(&mut self) {
        debug!("State: {} -> Disconnecting", self.state.name());
        self.state = ConnectionState::Disconnecting;
    }

    /// 检查是否应该重试
    pub fn should_retry(&self) -> bool {
        match &self.state {
            ConnectionState::Error {
                retry_at, attempt, ..
            } => *attempt < self.max_retries && Instant::now() >= *retry_at,
            _ => false,
        }
    }

    /// 获取连接时长（如果已连接）
    pub fn connection_duration(&self) -> Option<Duration> {
        match &self.state {
            ConnectionState::Connected { connected_at, .. } => Some(connected_at.elapsed()),
            _ => None,
        }
    }

    /// 重置状态机
    pub fn reset(&mut self) {
        info!("Resetting state machine");
        self.state = ConnectionState::Idle;
    }
}

impl Default for StateMachine {
    fn default() -> Self {
        Self::new(3, Duration::from_secs(2))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_state() {
        let sm = StateMachine::default();
        assert_eq!(sm.current_state().name(), "idle");
    }

    #[test]
    fn test_transition_to_connecting() {
        let mut sm = StateMachine::default();
        assert!(sm.transition_to_connecting().is_ok());
        assert_eq!(sm.current_state().name(), "connecting");
    }

    #[test]
    fn test_transition_to_connected() {
        let mut sm = StateMachine::default();
        sm.transition_to_connecting().unwrap();
        assert!(
            sm.transition_to_connected("session-123".to_string())
                .is_ok()
        );
        assert!(sm.current_state().is_connected());
    }

    #[test]
    fn test_transition_to_error() {
        let mut sm = StateMachine::default();
        sm.transition_to_connecting().unwrap();
        sm.transition_to_error("Connection failed".to_string());
        assert_eq!(sm.current_state().name(), "error");
    }

    #[test]
    fn test_retry_logic() {
        let mut sm = StateMachine::new(3, Duration::from_millis(10));
        sm.transition_to_connecting().unwrap();
        sm.transition_to_error("Test error".to_string());

        // 应该可以重试
        assert!(sm.current_state().can_retry());

        // 等待重试延迟
        std::thread::sleep(Duration::from_millis(20));
        assert!(sm.should_retry());

        // 重试
        assert!(sm.transition_to_connecting().is_ok());
    }

    #[test]
    fn test_max_retries() {
        let mut sm = StateMachine::new(2, Duration::from_millis(1));

        // 第一次连接失败
        sm.transition_to_connecting().unwrap();
        sm.transition_to_error("Error 1".to_string());

        // 第二次连接失败
        std::thread::sleep(Duration::from_millis(2));
        sm.transition_to_connecting().unwrap();
        sm.transition_to_error("Error 2".to_string());

        // 第三次应该失败（超过 max_retries）
        std::thread::sleep(Duration::from_millis(2));
        let result = sm.transition_to_connecting();
        assert!(result.is_err());
    }

    #[test]
    fn test_connection_duration() {
        let mut sm = StateMachine::default();
        sm.transition_to_connecting().unwrap();
        sm.transition_to_connected("test".to_string()).unwrap();

        std::thread::sleep(Duration::from_millis(10));
        let duration = sm.connection_duration();
        assert!(duration.is_some());
        assert!(duration.unwrap() >= Duration::from_millis(10));
    }

    #[test]
    fn test_reset() {
        let mut sm = StateMachine::default();
        sm.transition_to_connecting().unwrap();
        sm.transition_to_connected("test".to_string()).unwrap();

        sm.reset();
        assert_eq!(sm.current_state().name(), "idle");
    }
}
