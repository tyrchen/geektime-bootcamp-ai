//! 键盘模拟模块
//!
//! 使用 enigo 实现跨平台键盘输入模拟

use enigo::{Direction, Enigo, Key, Keyboard, Settings};
use thiserror::Error;
use tokio::time::{Duration, sleep};
use tracing::{debug, error};

#[derive(Error, Debug)]
pub enum KeyboardError {
    #[error("Failed to initialize keyboard controller")]
    InitFailed,

    #[error("Failed to type text: {0}")]
    TypeFailed(String),
}

type Result<T> = std::result::Result<T, KeyboardError>;

/// 键盘注入器
///
/// 使用操作系统的键盘模拟 API 输入文本
pub struct KeyboardInjector {
    enigo: Enigo,
}

impl KeyboardInjector {
    /// 创建新的键盘注入器
    pub fn new() -> Result<Self> {
        let enigo = Enigo::new(&Settings::default()).map_err(|_| KeyboardError::InitFailed)?;

        Ok(Self { enigo })
    }

    /// 输入文本
    ///
    /// # Arguments
    /// * `text` - 要输入的文本
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::input::KeyboardInjector;
    ///
    /// #[tokio::main]
    /// async fn main() {
    ///     let mut injector = KeyboardInjector::new().unwrap();
    ///     injector.type_text("Hello, world!").await.unwrap();
    /// }
    /// ```
    pub async fn type_text(&mut self, text: &str) -> Result<()> {
        debug!("Typing text: {} chars", text.len());

        // enigo 0.6 使用 text() 方法输入文本
        self.enigo
            .text(text)
            .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;

        // 短暂延迟确保输入完成
        sleep(Duration::from_millis(10)).await;

        Ok(())
    }

    /// 模拟粘贴快捷键
    ///
    /// - macOS: Cmd+V
    /// - Windows/Linux: Ctrl+V
    pub fn simulate_paste(&mut self) -> Result<()> {
        debug!("Simulating paste shortcut");

        #[cfg(target_os = "macos")]
        {
            // 添加错误处理，避免 enigo 崩溃导致程序退出
            if let Err(e) = self.enigo.key(Key::Meta, Direction::Press) {
                error!("Failed to press Meta key: {}", e);
                return Err(KeyboardError::TypeFailed(e.to_string()));
            }

            if let Err(e) = self.enigo.key(Key::Unicode('v'), Direction::Click) {
                error!("Failed to click 'v' key: {}", e);
                // 尝试释放 Meta 键避免卡住
                let _ = self.enigo.key(Key::Meta, Direction::Release);
                return Err(KeyboardError::TypeFailed(e.to_string()));
            }

            if let Err(e) = self.enigo.key(Key::Meta, Direction::Release) {
                error!("Failed to release Meta key: {}", e);
                return Err(KeyboardError::TypeFailed(e.to_string()));
            }

            debug!("Paste shortcut simulated successfully");
        }

        #[cfg(not(target_os = "macos"))]
        {
            self.enigo
                .key(Key::Control, Direction::Press)
                .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
            self.enigo
                .key(Key::Unicode('v'), Direction::Click)
                .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
            self.enigo
                .key(Key::Control, Direction::Release)
                .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
        }

        Ok(())
    }

    /// 模拟回车键
    pub fn simulate_enter(&mut self) -> Result<()> {
        self.enigo
            .key(Key::Return, Direction::Click)
            .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
        Ok(())
    }

    /// 模拟退格键
    pub fn simulate_backspace(&mut self) -> Result<()> {
        self.enigo
            .key(Key::Backspace, Direction::Click)
            .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
        Ok(())
    }

    /// 模拟删除键
    pub fn simulate_delete(&mut self) -> Result<()> {
        self.enigo
            .key(Key::Delete, Direction::Click)
            .map_err(|e| KeyboardError::TypeFailed(e.to_string()))?;
        Ok(())
    }
}

impl Default for KeyboardInjector {
    fn default() -> Self {
        Self::new().unwrap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[ignore] // 需要 GUI 环境
    fn test_keyboard_injector_creation() {
        let injector = KeyboardInjector::new();
        assert!(injector.is_ok());
    }

    #[tokio::test]
    #[ignore] // 需要 GUI 环境且会实际输入文本
    async fn test_type_text() {
        let mut injector = KeyboardInjector::new().unwrap();
        let result = injector.type_text("test").await;
        assert!(result.is_ok());
    }

    #[test]
    #[ignore] // 需要 GUI 环境
    fn test_simulate_paste() {
        let mut injector = KeyboardInjector::new().unwrap();
        let _ = injector.simulate_paste();
        // 无法自动验证，需要手动测试
    }

    #[test]
    #[ignore] // 需要 GUI 环境
    fn test_simulate_enter() {
        let mut injector = KeyboardInjector::new().unwrap();
        let _ = injector.simulate_enter();
    }

    #[test]
    #[ignore] // 需要 GUI 环境
    fn test_default() {
        let _injector = KeyboardInjector::default();
    }
}
