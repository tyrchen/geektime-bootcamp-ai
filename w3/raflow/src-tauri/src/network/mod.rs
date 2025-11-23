//! 网络通信模块
//!
//! 包含 WebSocket 客户端、协议定义、状态管理等功能

mod client;
mod manager;
mod protocol;
mod state_machine;

pub use client::{ClientConfig, ClientError, ScribeClient, WsSink, WsStream};
pub use manager::{ManagerError, NetworkManager};
pub use protocol::{ClientMessage, ServerMessage};
pub use state_machine::{ConnectionState, StateError, StateMachine};
