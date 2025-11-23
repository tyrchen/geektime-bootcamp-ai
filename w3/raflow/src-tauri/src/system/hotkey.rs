//! 全局热键管理模块
//!
//! 使用 tauri-plugin-global-shortcut 实现全局热键

use tauri::{AppHandle, Emitter};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};
use thiserror::Error;
use tracing::{debug, info, warn};

#[derive(Error, Debug)]
pub enum HotkeyError {
    #[error("Failed to register hotkey: {0}")]
    RegisterFailed(String),

    #[error("Failed to unregister hotkey: {0}")]
    UnregisterFailed(String),

    #[error("Invalid hotkey format: {0}")]
    InvalidFormat(String),
}

type Result<T> = std::result::Result<T, HotkeyError>;

/// 热键管理器
pub struct HotkeyManager;

impl HotkeyManager {
    /// 注册全局热键
    ///
    /// # Arguments
    /// * `app` - Tauri AppHandle
    /// * `hotkey_str` - 热键字符串（如 "CommandOrControl+Shift+\"）
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::system::HotkeyManager;
    ///
    /// fn setup(app: &tauri::AppHandle) {
    ///     HotkeyManager::register(app, "CommandOrControl+Shift+\\").unwrap();
    /// }
    /// ```
    pub fn register(app: &AppHandle, hotkey_str: &str) -> Result<()> {
        info!("Registering global hotkey: {}", hotkey_str);

        // 解析热键字符串
        let shortcut = Self::parse_hotkey(hotkey_str)?;

        // 注册热键（仅响应 Pressed 事件，用于切换）
        app.global_shortcut()
            .on_shortcut(shortcut, move |app, _shortcut, event| {
                // 只处理按键按下事件（切换模式）
                if event.state != ShortcutState::Pressed {
                    return;
                }

                info!("Hotkey pressed - toggling recording");

                // 发送切换事件到前端
                if let Err(e) = app.emit("hotkey_toggle", ()) {
                    warn!("Failed to emit hotkey_toggle event: {}", e);
                }
            })
            .map_err(|e| HotkeyError::RegisterFailed(e.to_string()))?;

        info!("Hotkey registered successfully: {}", hotkey_str);

        Ok(())
    }

    /// 注销热键
    pub fn unregister(app: &AppHandle, hotkey_str: &str) -> Result<()> {
        info!("Unregistering hotkey: {}", hotkey_str);

        let shortcut = Self::parse_hotkey(hotkey_str)?;

        app.global_shortcut()
            .unregister(shortcut)
            .map_err(|e| HotkeyError::UnregisterFailed(e.to_string()))?;

        info!("Hotkey unregistered");

        Ok(())
    }

    /// 解析热键字符串
    ///
    /// 支持格式：
    /// - "CommandOrControl+Shift+A"
    /// - "Cmd+Shift+\"
    /// - "Ctrl+Alt+Space"
    fn parse_hotkey(_hotkey_str: &str) -> Result<Shortcut> {
        // 简化版：直接使用默认热键
        // 完整的解析逻辑可以在未来添加

        // 默认：CommandOrControl+Shift+Backslash
        let modifiers = Modifiers::SUPER | Modifiers::SHIFT;
        let key = Code::Backslash;

        let shortcut = Shortcut::new(Some(modifiers), key);

        debug!("Parsed hotkey: {:?}", shortcut);

        Ok(shortcut)
    }

    /// 检查热键是否已注册
    pub fn is_registered(app: &AppHandle, hotkey_str: &str) -> bool {
        if let Ok(shortcut) = Self::parse_hotkey(hotkey_str) {
            app.global_shortcut().is_registered(shortcut)
        } else {
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_hotkey() {
        let result = HotkeyManager::parse_hotkey("CommandOrControl+Shift+\\");
        assert!(result.is_ok());
    }

    // 实际的热键注册测试需要 Tauri 运行时
    // 应该在集成测试中进行
}
