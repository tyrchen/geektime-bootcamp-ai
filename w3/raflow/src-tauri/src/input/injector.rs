//! 文本注入器模块
//!
//! 整合键盘和剪贴板策略，实现智能文本注入

use super::{
    clipboard::{ClipboardError, ClipboardInjector},
    focus::{FocusError, FocusManager},
    keyboard::{KeyboardError, KeyboardInjector},
};
use crate::system::WindowInfo;
use tauri::AppHandle;
use thiserror::Error;
use tracing::{debug, info, warn};

#[derive(Error, Debug)]
pub enum InjectorError {
    #[error("Keyboard error: {0}")]
    Keyboard(#[from] KeyboardError),

    #[error("Clipboard error: {0}")]
    Clipboard(#[from] ClipboardError),

    #[error("Focus error: {0}")]
    Focus(#[from] FocusError),

    #[error("Target window is blacklisted: {0}")]
    Blacklisted(String),

    #[error("Text too long: {0} chars (max: {1})")]
    TextTooLong(usize, usize),
}

type Result<T> = std::result::Result<T, InjectorError>;

/// 注入策略
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum InjectionStrategy {
    /// 键盘模拟（适合短文本）
    Keyboard,
    /// 剪贴板（适合长文本）
    Clipboard,
}

/// 注入配置
#[derive(Debug, Clone)]
pub struct InjectionConfig {
    /// 键盘策略的最大字符数阈值
    pub keyboard_max_chars: usize,
    /// 每个字符的输入延迟（毫秒）
    pub typing_delay_ms: u64,
    /// 焦点归还等待时间（毫秒）
    pub focus_wait_ms: u64,
    /// 是否启用黑名单检查
    pub enable_blacklist: bool,
    /// 最大文本长度限制
    pub max_text_length: usize,
    /// 是否自动模拟粘贴快捷键（false 则只写入剪贴板，不自动粘贴）
    pub auto_paste: bool,
}

impl Default for InjectionConfig {
    fn default() -> Self {
        Self {
            keyboard_max_chars: 10,
            typing_delay_ms: 5,
            focus_wait_ms: 50,
            enable_blacklist: true,
            max_text_length: 10000,
            auto_paste: false, // 默认禁用自动粘贴，避免 enigo 导致程序退出
        }
    }
}

/// 文本注入器
///
/// 智能选择注入策略并执行文本注入
pub struct TextInjector {
    keyboard: KeyboardInjector,
    clipboard: ClipboardInjector,
    focus: FocusManager,
    config: InjectionConfig,
}

impl TextInjector {
    /// 创建新的文本注入器
    ///
    /// # Arguments
    /// * `app` - Tauri AppHandle
    pub fn new(app: AppHandle) -> Result<Self> {
        Ok(Self {
            keyboard: KeyboardInjector::new()?,
            clipboard: ClipboardInjector::new(app.clone()),
            focus: FocusManager::new(app),
            config: InjectionConfig::default(),
        })
    }

    /// 使用自定义配置创建注入器
    pub fn with_config(app: AppHandle, config: InjectionConfig) -> Result<Self> {
        Ok(Self {
            keyboard: KeyboardInjector::new()?,
            clipboard: ClipboardInjector::new(app.clone()),
            focus: FocusManager::new(app),
            config,
        })
    }

    /// 注入文本到目标窗口
    ///
    /// # Arguments
    /// * `text` - 要注入的文本
    /// * `window` - 目标窗口信息
    ///
    /// # Returns
    /// * `Ok(InjectionStrategy)` - 成功注入，返回使用的策略
    /// * `Err(InjectorError)` - 注入失败
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::input::TextInjector;
    /// use raflow_lib::system::{WindowInfo, WindowTracker};
    ///
    /// async fn inject_text(app: tauri::AppHandle) {
    ///     let mut injector = TextInjector::new(app).unwrap();
    ///     let window = WindowTracker::get_current_window().unwrap();
    ///     injector.inject("Hello, world!", &window).await.unwrap();
    /// }
    /// ```
    pub async fn inject(&mut self, text: &str, window: &WindowInfo) -> Result<InjectionStrategy> {
        info!(
            "Injecting text: {} chars to {}",
            text.len(),
            window.app_name
        );

        // 1. 检查文本长度
        if text.len() > self.config.max_text_length {
            return Err(InjectorError::TextTooLong(
                text.len(),
                self.config.max_text_length,
            ));
        }

        // 2. 黑名单检查
        if self.config.enable_blacklist && window.is_blacklisted() {
            warn!("Target window is blacklisted: {}", window.app_name);
            return Err(InjectorError::Blacklisted(window.app_name.clone()));
        }

        // 3. 确保焦点在目标窗口
        self.focus
            .ensure_target_focused(self.config.focus_wait_ms)
            .await?;

        // 4. 选择注入策略
        let strategy = self.select_strategy(text);
        debug!("Selected strategy: {:?}", strategy);

        // 5. 执行注入
        match strategy {
            InjectionStrategy::Keyboard => {
                self.inject_via_keyboard(text).await?;
            }
            InjectionStrategy::Clipboard => {
                self.inject_via_clipboard(text).await?;
            }
        }

        info!("Text injected successfully using {:?}", strategy);

        Ok(strategy)
    }

    /// 选择注入策略
    ///
    /// 根据文本长度自动选择最佳策略
    fn select_strategy(&self, text: &str) -> InjectionStrategy {
        if text.len() <= self.config.keyboard_max_chars {
            InjectionStrategy::Keyboard
        } else {
            InjectionStrategy::Clipboard
        }
    }

    /// 通过键盘模拟注入（短文本）
    async fn inject_via_keyboard(&mut self, text: &str) -> Result<()> {
        debug!("Injecting via keyboard: {} chars", text.len());
        self.keyboard.type_text(text).await?;
        Ok(())
    }

    /// 通过剪贴板注入（长文本）
    async fn inject_via_clipboard(&self, text: &str) -> Result<()> {
        debug!("Injecting via clipboard: {} chars", text.len());
        self.clipboard.inject_via_clipboard(text, self.config.auto_paste).await?;
        Ok(())
    }

    /// 更新配置
    pub fn set_config(&mut self, config: InjectionConfig) {
        self.config = config;
    }

    /// 获取当前配置
    pub fn config(&self) -> &InjectionConfig {
        &self.config
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_injection_config_default() {
        let config = InjectionConfig::default();
        assert_eq!(config.keyboard_max_chars, 10);
        assert_eq!(config.typing_delay_ms, 5);
        assert_eq!(config.focus_wait_ms, 50);
        assert!(config.enable_blacklist);
    }

    #[test]
    fn test_injection_strategy_selection() {
        let config = InjectionConfig::default();

        // 模拟策略选择逻辑
        let short_text = "Hello";
        let strategy = if short_text.len() <= config.keyboard_max_chars {
            InjectionStrategy::Keyboard
        } else {
            InjectionStrategy::Clipboard
        };
        assert_eq!(strategy, InjectionStrategy::Keyboard);

        let long_text = "This is a very long text that should use clipboard";
        let strategy = if long_text.len() <= config.keyboard_max_chars {
            InjectionStrategy::Keyboard
        } else {
            InjectionStrategy::Clipboard
        };
        assert_eq!(strategy, InjectionStrategy::Clipboard);
    }

    #[test]
    fn test_injector_error_types() {
        let err = InjectorError::Blacklisted("1Password".to_string());
        assert!(err.to_string().contains("blacklisted"));

        let err = InjectorError::TextTooLong(20000, 10000);
        assert!(err.to_string().contains("too long"));
    }

    // 实际的注入测试需要 Tauri 运行时和 GUI 环境
    // 应该在集成测试中进行
}
