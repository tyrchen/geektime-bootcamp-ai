//! 配置管理模块
//!
//! 使用 Tauri Store 插件持久化配置

use serde::{Deserialize, Serialize};
use tauri::AppHandle;
use tauri_plugin_store::StoreExt;
use thiserror::Error;
use tracing::{debug, info};

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("Failed to load config: {0}")]
    LoadFailed(String),

    #[error("Failed to save config: {0}")]
    SaveFailed(String),

    #[error("Store not available")]
    StoreNotAvailable,
}

type Result<T> = std::result::Result<T, ConfigError>;

const STORE_PATH: &str = "config.json";

/// 应用配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_key: String,
    pub hotkey: String,
    pub language: String,
    pub keyboard_max_chars: usize,
    pub enable_blacklist: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            hotkey: "CommandOrControl+Shift+\\".to_string(),
            language: "zh".to_string(),
            keyboard_max_chars: 10,
            enable_blacklist: true,
        }
    }
}

/// 配置管理器
pub struct ConfigManager;

impl ConfigManager {
    /// 加载配置
    ///
    /// # Arguments
    /// * `app` - Tauri AppHandle
    pub fn load(app: &AppHandle) -> Result<AppConfig> {
        debug!("Loading config from store");

        let store = app
            .store(STORE_PATH)
            .map_err(|e| ConfigError::LoadFailed(e.to_string()))?;

        // 尝试从 store 读取配置
        let api_key = store
            .get("api_key")
            .and_then(|v| v.as_str().map(|s| s.to_string()))
            .unwrap_or_default();

        // 如果没有 API Key，返回默认配置
        if api_key.is_empty() {
            info!("No existing config, using defaults");
            return Ok(AppConfig::default());
        }

        let config = AppConfig {
            api_key,
            hotkey: store
                .get("hotkey")
                .and_then(|v| v.as_str().map(|s| s.to_string()))
                .unwrap_or_else(|| "CommandOrControl+Shift+\\".to_string()),
            language: store
                .get("language")
                .and_then(|v| v.as_str().map(|s| s.to_string()))
                .unwrap_or_else(|| "zh".to_string()),
            keyboard_max_chars: store
                .get("keyboard_max_chars")
                .and_then(|v| v.as_u64())
                .unwrap_or(10) as usize,
            enable_blacklist: store
                .get("enable_blacklist")
                .and_then(|v| v.as_bool())
                .unwrap_or(true),
        };

        info!("Config loaded: language = {}", config.language);
        Ok(config)
    }

    /// 保存配置
    ///
    /// # Arguments
    /// * `app` - Tauri AppHandle
    /// * `config` - 要保存的配置
    pub fn save(app: &AppHandle, config: &AppConfig) -> Result<()> {
        info!("Saving config: language = {}", config.language);

        let store = app
            .store(STORE_PATH)
            .map_err(|e| ConfigError::SaveFailed(e.to_string()))?;

        // 保存各个字段
        store.set("api_key", serde_json::json!(config.api_key));
        store.set("hotkey", serde_json::json!(config.hotkey));
        store.set("language", serde_json::json!(config.language));
        store.set(
            "keyboard_max_chars",
            serde_json::json!(config.keyboard_max_chars),
        );
        store.set(
            "enable_blacklist",
            serde_json::json!(config.enable_blacklist),
        );

        // 持久化到磁盘
        store
            .save()
            .map_err(|e| ConfigError::SaveFailed(e.to_string()))?;

        info!("Config saved successfully");

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_config_default() {
        let config = AppConfig::default();
        assert_eq!(config.language, "zh");
        assert_eq!(config.keyboard_max_chars, 10);
        assert!(config.enable_blacklist);
        assert_eq!(config.hotkey, "CommandOrControl+Shift+\\");
    }

    #[test]
    fn test_app_config_serialization() {
        let config = AppConfig {
            api_key: "test-key-123".to_string(),
            hotkey: "Cmd+Shift+A".to_string(),
            language: "en".to_string(),
            keyboard_max_chars: 20,
            enable_blacklist: false,
        };

        let json = serde_json::to_string(&config).unwrap();
        let deserialized: AppConfig = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.api_key, config.api_key);
        assert_eq!(deserialized.language, "en");
        assert_eq!(deserialized.keyboard_max_chars, 20);
        assert!(!deserialized.enable_blacklist);
    }

    // 实际的 load/save 测试需要 Tauri 运行时
    // 应该在集成测试中进行
}
