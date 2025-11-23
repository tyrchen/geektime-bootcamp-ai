//! 活跃窗口追踪模块
//!
//! 获取当前活跃窗口信息，用于智能文本注入

use active_win_pos_rs::{ActiveWindow, get_active_window};
use serde::{Deserialize, Serialize};
use thiserror::Error;
use tracing::{debug, info};

#[derive(Error, Debug)]
pub enum WindowError {
    #[error("Failed to get active window: {0}")]
    GetWindowFailed(String),

    #[error("No active window found")]
    NoActiveWindow,
}

type Result<T> = std::result::Result<T, WindowError>;

/// 窗口信息
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct WindowInfo {
    /// 应用名称
    pub app_name: String,
    /// 窗口标题
    pub title: String,
    /// 进程 ID
    pub process_id: u32,
    /// 窗口位置和大小 (x, y, width, height)
    pub position: (i32, i32, u32, u32),
}

impl WindowInfo {
    /// 从 active-win-pos-rs 的 ActiveWindow 转换
    pub fn from_active_window(window: ActiveWindow) -> Self {
        Self {
            app_name: window.app_name,
            title: window.title,
            process_id: window.process_id as u32,
            position: (
                window.position.x as i32,
                window.position.y as i32,
                window.position.width as u32,
                window.position.height as u32,
            ),
        }
    }

    /// 检查是否为黑名单应用
    pub fn is_blacklisted(&self) -> bool {
        WindowTracker::is_blacklisted(self)
    }
}

/// 窗口追踪器
pub struct WindowTracker;

impl WindowTracker {
    /// 获取当前活跃窗口信息
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::system::WindowTracker;
    ///
    /// let window = WindowTracker::get_current_window().unwrap();
    /// println!("Current app: {}", window.app_name);
    /// ```
    pub fn get_current_window() -> Result<WindowInfo> {
        let active = get_active_window()
            .map_err(|_| WindowError::GetWindowFailed("Failed to get active window".to_string()))?;

        info!("Active window: {} - {}", active.app_name, active.title);

        Ok(WindowInfo::from_active_window(active))
    }

    /// 检查窗口是否在黑名单中
    ///
    /// 黑名单应用不应该接收自动文本注入（如密码管理器）
    pub fn is_blacklisted(window: &WindowInfo) -> bool {
        const BLACKLIST: &[&str] = &[
            "1Password",
            "Bitwarden",
            "Keychain Access",
            "LastPass",
            "KeePass",
            "Dashlane",
        ];

        BLACKLIST.iter().any(|&app| window.app_name.contains(app))
    }

    /// 列出所有应该排除的应用
    pub fn get_blacklist() -> Vec<String> {
        vec![
            "1Password".to_string(),
            "Bitwarden".to_string(),
            "Keychain Access".to_string(),
            "LastPass".to_string(),
            "KeePass".to_string(),
            "Dashlane".to_string(),
        ]
    }

    /// 检查是否为终端应用
    pub fn is_terminal(window: &WindowInfo) -> bool {
        const TERMINALS: &[&str] = &[
            "Terminal",
            "iTerm",
            "Alacritty",
            "Kitty",
            "WezTerm",
            "Hyper",
        ];

        TERMINALS.iter().any(|&term| window.app_name.contains(term))
    }

    /// 监听窗口变化（轮询方式）
    ///
    /// # Arguments
    /// * `interval_ms` - 轮询间隔（毫秒）
    /// * `callback` - 窗口变化时的回调函数
    pub async fn watch_window<F>(interval_ms: u64, mut callback: F)
    where
        F: FnMut(WindowInfo) + Send + 'static,
    {
        let mut last_window: Option<WindowInfo> = None;

        loop {
            if let Ok(current) = Self::get_current_window() {
                // 检查窗口是否变化
                if last_window.as_ref() != Some(&current) {
                    debug!(
                        "Window changed: {} -> {}",
                        last_window
                            .as_ref()
                            .map(|w| w.app_name.as_str())
                            .unwrap_or("None"),
                        current.app_name
                    );
                    callback(current.clone());
                    last_window = Some(current);
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(interval_ms)).await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[ignore] // 需要 GUI 环境
    fn test_get_current_window() {
        let window = WindowTracker::get_current_window();
        assert!(window.is_ok());

        let win = window.unwrap();
        println!("Current window: {} - {}", win.app_name, win.title);
        assert!(!win.app_name.is_empty());
    }

    #[test]
    fn test_is_blacklisted() {
        let password_manager = WindowInfo {
            app_name: "1Password 8".to_string(),
            title: "Unlock 1Password".to_string(),
            process_id: 12345,
            position: (0, 0, 800, 600),
        };

        assert!(WindowTracker::is_blacklisted(&password_manager));
        assert!(password_manager.is_blacklisted());
    }

    #[test]
    fn test_is_not_blacklisted() {
        let chrome = WindowInfo {
            app_name: "Google Chrome".to_string(),
            title: "GitHub".to_string(),
            process_id: 12345,
            position: (0, 0, 1920, 1080),
        };

        assert!(!WindowTracker::is_blacklisted(&chrome));
    }

    #[test]
    fn test_is_terminal() {
        let terminal = WindowInfo {
            app_name: "iTerm2".to_string(),
            title: "bash".to_string(),
            process_id: 12345,
            position: (0, 0, 800, 600),
        };

        assert!(WindowTracker::is_terminal(&terminal));
    }

    #[test]
    fn test_get_blacklist() {
        let blacklist = WindowTracker::get_blacklist();
        assert!(!blacklist.is_empty());
        assert!(blacklist.contains(&"1Password".to_string()));
    }

    #[tokio::test]
    #[ignore] // 长时间运行测试
    async fn test_watch_window() {
        use std::sync::Arc;
        use std::sync::atomic::{AtomicUsize, Ordering};

        let counter = Arc::new(AtomicUsize::new(0));
        let counter_clone = counter.clone();

        let watch_task = tokio::spawn(async move {
            WindowTracker::watch_window(100, move |_window| {
                counter_clone.fetch_add(1, Ordering::Relaxed);
            })
            .await;
        });

        // 运行 1 秒
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        watch_task.abort();

        // 应该至少触发一次回调
        assert!(counter.load(Ordering::Relaxed) > 0);
    }
}
