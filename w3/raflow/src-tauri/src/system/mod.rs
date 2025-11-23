//! 系统集成模块
//!
//! 包含窗口追踪、热键管理、系统托盘等系统级功能

pub mod hotkey;
pub mod tray;
pub mod window;

pub use hotkey::{HotkeyError, HotkeyManager};
pub use tray::setup_tray;
pub use window::{WindowError, WindowInfo, WindowTracker};
