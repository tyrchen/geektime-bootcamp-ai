//! 焦点管理模块
//!
//! 管理悬浮窗和目标应用之间的焦点切换

use tauri::{AppHandle, Manager};
use thiserror::Error;
use tokio::time::{Duration, sleep};
use tracing::{debug, warn};

#[derive(Error, Debug)]
pub enum FocusError {
    #[error("Window not found: {0}")]
    WindowNotFound(String),

    #[error("Failed to hide window: {0}")]
    HideFailed(String),

    #[error("Failed to show window: {0}")]
    ShowFailed(String),

    #[error("Failed to focus window: {0}")]
    FocusFailed(String),
}

type Result<T> = std::result::Result<T, FocusError>;

/// 焦点管理器
///
/// 确保文本注入时焦点在正确的窗口
pub struct FocusManager {
    app: AppHandle,
}

impl FocusManager {
    /// 创建新的焦点管理器
    pub fn new(app: AppHandle) -> Self {
        Self { app }
    }

    /// 隐藏悬浮窗并等待焦点归还
    ///
    /// 隐藏悬浮窗后，系统会自动将焦点归还给之前的活跃窗口
    ///
    /// # Arguments
    /// * `wait_ms` - 等待焦点归还的时间（毫秒）
    pub async fn ensure_target_focused(&self, wait_ms: u64) -> Result<()> {
        debug!("Ensuring target window has focus");

        // 获取 overlay 窗口
        if let Some(overlay) = self.app.get_webview_window("overlay") {
            // 隐藏悬浮窗
            overlay
                .hide()
                .map_err(|e| FocusError::HideFailed(e.to_string()))?;

            debug!("Overlay hidden");
        } else {
            warn!("Overlay window not found");
        }

        // 等待系统将焦点归还给目标应用
        // 增加等待时间，确保焦点真正切换
        let extended_wait = wait_ms.max(200); // 至少等待 200ms
        sleep(Duration::from_millis(extended_wait)).await;

        debug!("Focus should be on target window now (waited {}ms)", extended_wait);

        Ok(())
    }

    /// 显示悬浮窗
    pub fn show_overlay(&self) -> Result<()> {
        debug!("Showing overlay window");

        if let Some(overlay) = self.app.get_webview_window("overlay") {
            overlay
                .show()
                .map_err(|e| FocusError::ShowFailed(e.to_string()))?;

            overlay
                .set_focus()
                .map_err(|e| FocusError::FocusFailed(e.to_string()))?;

            debug!("Overlay shown and focused");
        } else {
            return Err(FocusError::WindowNotFound("overlay".to_string()));
        }

        Ok(())
    }

    /// 隐藏悬浮窗
    pub fn hide_overlay(&self) -> Result<()> {
        debug!("Hiding overlay window");

        if let Some(overlay) = self.app.get_webview_window("overlay") {
            overlay
                .hide()
                .map_err(|e| FocusError::HideFailed(e.to_string()))?;

            debug!("Overlay hidden");
        }

        Ok(())
    }

    /// 检查悬浮窗是否可见
    pub fn is_overlay_visible(&self) -> Result<bool> {
        if let Some(overlay) = self.app.get_webview_window("overlay") {
            overlay
                .is_visible()
                .map_err(|e| FocusError::WindowNotFound(e.to_string()))
        } else {
            Ok(false)
        }
    }

    /// 切换悬浮窗可见性
    pub fn toggle_overlay(&self) -> Result<()> {
        if self.is_overlay_visible()? {
            self.hide_overlay()
        } else {
            self.show_overlay()
        }
    }

    /// 显示设置窗口
    pub fn show_settings(&self) -> Result<()> {
        debug!("Showing settings window");

        if let Some(main_window) = self.app.get_webview_window("main") {
            main_window
                .show()
                .map_err(|e| FocusError::ShowFailed(e.to_string()))?;

            main_window
                .set_focus()
                .map_err(|e| FocusError::FocusFailed(e.to_string()))?;

            debug!("Settings window shown and focused");
        } else {
            return Err(FocusError::WindowNotFound("main".to_string()));
        }

        Ok(())
    }

    /// 隐藏设置窗口
    pub fn hide_settings(&self) -> Result<()> {
        debug!("Hiding settings window");

        if let Some(main_window) = self.app.get_webview_window("main") {
            main_window
                .hide()
                .map_err(|e| FocusError::HideFailed(e.to_string()))?;

            debug!("Settings window hidden");
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_focus_error_types() {
        let err = FocusError::WindowNotFound("test".to_string());
        assert!(err.to_string().contains("Window not found"));

        let err = FocusError::HideFailed("test".to_string());
        assert!(err.to_string().contains("Failed to hide window"));

        let err = FocusError::ShowFailed("test".to_string());
        assert!(err.to_string().contains("Failed to show window"));
    }

    // 实际的焦点管理测试需要 Tauri 运行时环境
    // 应该在集成测试或 E2E 测试中进行
}
