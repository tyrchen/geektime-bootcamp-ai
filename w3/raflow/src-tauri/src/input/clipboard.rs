//! 剪贴板注入模块
//!
//! 通过剪贴板策略注入长文本

use super::keyboard::KeyboardInjector;
use tauri::AppHandle;
use tauri_plugin_clipboard_manager::ClipboardExt;
use thiserror::Error;
use tokio::time::{Duration, sleep};
use tracing::{debug, warn};

#[derive(Error, Debug)]
pub enum ClipboardError {
    #[error("Failed to read clipboard: {0}")]
    ReadFailed(String),

    #[error("Failed to write clipboard: {0}")]
    WriteFailed(String),

    #[error("Keyboard error: {0}")]
    Keyboard(#[from] super::keyboard::KeyboardError),
}

type Result<T> = std::result::Result<T, ClipboardError>;

/// 剪贴板注入器
///
/// 使用剪贴板策略注入文本（适合长文本）
pub struct ClipboardInjector {
    app: AppHandle,
}

impl ClipboardInjector {
    /// 创建新的剪贴板注入器
    ///
    /// # Arguments
    /// * `app` - Tauri AppHandle
    pub fn new(app: AppHandle) -> Self {
        Self { app }
    }

    /// 通过剪贴板注入文本
    ///
    /// # 流程
    /// 1. 保存当前剪贴板内容
    /// 2. 写入新文本到剪贴板
    /// 3. (可选) 模拟 Cmd+V/Ctrl+V 粘贴
    /// 4. 等待粘贴完成
    /// 5. 恢复旧剪贴板内容
    ///
    /// # Arguments
    /// * `text` - 要注入的文本
    /// * `auto_paste` - 是否自动模拟粘贴快捷键
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::input::ClipboardInjector;
    ///
    /// async fn inject_text(app: tauri::AppHandle) {
    ///     let injector = ClipboardInjector::new(app);
    ///     injector.inject_via_clipboard("Long text here...", true).await.unwrap();
    /// }
    /// ```
    pub async fn inject_via_clipboard(&self, text: &str, auto_paste: bool) -> Result<()> {
        debug!("Injecting via clipboard: {} chars", text.len());

        // 1. 保存当前剪贴板内容
        let old_content = self.app.clipboard().read_text().ok();

        if old_content.is_some() {
            debug!("Saved old clipboard content");
        }

        // 2. 写入新文本到剪贴板
        self.app
            .clipboard()
            .write_text(text)
            .map_err(|e| ClipboardError::WriteFailed(e.to_string()))?;

        debug!("Wrote new text to clipboard");

        // 3. 模拟粘贴快捷键（如果启用）
        if auto_paste {
            let mut keyboard = KeyboardInjector::new()?;
            keyboard.simulate_paste()?;
            debug!("Simulated paste shortcut");
        } else {
            debug!("Skipped paste simulation (auto_paste=false)");
        }

        // 4. 等待粘贴完成（根据文本长度动态调整）
        let wait_time = (text.len() / 100).clamp(1, 5); // 1-5 秒
        sleep(Duration::from_millis(wait_time as u64 * 100)).await;

        // 5. 恢复旧剪贴板内容
        if let Some(old) = old_content {
            if let Err(e) = self.app.clipboard().write_text(&old) {
                warn!("Failed to restore old clipboard: {}", e);
            } else {
                debug!("Restored old clipboard content");
            }
        }

        Ok(())
    }

    /// 读取当前剪贴板内容
    pub fn read(&self) -> Result<String> {
        self.app
            .clipboard()
            .read_text()
            .map_err(|e| ClipboardError::ReadFailed(e.to_string()))
    }

    /// 写入文本到剪贴板
    pub fn write(&self, text: &str) -> Result<()> {
        self.app
            .clipboard()
            .write_text(text)
            .map_err(|e| ClipboardError::WriteFailed(e.to_string()))
    }

    /// 清空剪贴板
    pub fn clear(&self) -> Result<()> {
        self.app
            .clipboard()
            .write_text("")
            .map_err(|e| ClipboardError::WriteFailed(e.to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // 注意：剪贴板测试需要 Tauri AppHandle，在单元测试中无法创建
    // 这些测试应该在集成测试或 E2E 测试中进行

    #[test]
    fn test_clipboard_error_types() {
        let err = ClipboardError::ReadFailed("test".to_string());
        assert!(err.to_string().contains("Failed to read clipboard"));

        let err = ClipboardError::WriteFailed("test".to_string());
        assert!(err.to_string().contains("Failed to write clipboard"));
    }
}
