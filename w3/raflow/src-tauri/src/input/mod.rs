//! 输入注入模块
//!
//! 包含键盘模拟、剪贴板操作、焦点管理等功能

pub mod clipboard;
pub mod focus;
pub mod injector;
pub mod keyboard;

pub use clipboard::{ClipboardError, ClipboardInjector};
pub use focus::{FocusError, FocusManager};
pub use injector::{InjectionConfig, InjectionStrategy, InjectorError, TextInjector};
pub use keyboard::{KeyboardError, KeyboardInjector};
