//! 系统集成模块
//!
//! 包含窗口追踪、热键管理等系统级功能

pub mod window;

pub use window::{WindowError, WindowInfo, WindowTracker};
