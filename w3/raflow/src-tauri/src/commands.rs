//! Tauri 命令模块
//!
//! 定义前端可以调用的后端命令

use tauri::{command, AppHandle, Manager, State};
use tracing::{debug, error, info, warn};

use crate::AppState;
use crate::config::ConfigManager;
use crate::state::RecordingState;

// 重导出 AppConfig 为 Config（兼容前端）
pub use crate::config::AppConfig as Config;

/// 获取配置
#[command]
pub async fn get_config(app: AppHandle, _state: State<'_, AppState>) -> Result<Config, String> {
    debug!("Getting config");

    ConfigManager::load(&app).map_err(|e| {
        error!("Failed to load config: {}", e);
        e.to_string()
    })
}

/// 保存配置
#[command]
pub async fn save_config(
    app: AppHandle,
    _state: State<'_, AppState>,
    config: Config,
) -> Result<(), String> {
    info!("Saving config: language = {}", config.language);

    ConfigManager::save(&app, &config).map_err(|e| {
        error!("Failed to save config: {}", e);
        e.to_string()
    })
}

/// 开始录音
#[command]
pub async fn start_recording(app: AppHandle, state: State<'_, AppState>) -> Result<(), String> {
    info!("Start recording command");

    // 检查是否已在录音
    if state.get_state() == RecordingState::Recording {
        warn!("Already recording");
        return Err("Already recording".to_string());
    }

    // 加载配置
    let config = ConfigManager::load(&app).map_err(|e| e.to_string())?;
    if config.api_key.is_empty() {
        warn!("API Key not configured");
        return Err("请先配置 API Key".to_string());
    }

    // 发送开始命令到后台控制任务
    state.start_recording(config).await?;

    info!("Recording started");

    Ok(())
}

/// 停止录音
#[command]
pub async fn stop_recording(state: State<'_, AppState>) -> Result<(), String> {
    info!("Stop recording command");

    // 发送停止命令到后台控制任务
    state.stop_recording().await?;

    info!("Recording stopped");

    Ok(())
}

/// 切换录音状态（热键触发）
#[command]
pub async fn toggle_recording(app: AppHandle, state: State<'_, AppState>) -> Result<(), String> {
    info!("Toggle recording command");

    let current_state = state.get_state();

    match current_state {
        RecordingState::Idle => {
            // 当前空闲，开始录音
            info!("Current idle, starting recording");

            // 显示悬浮窗
            if let Some(overlay) = app.get_webview_window("overlay") {
                let _ = overlay.show();
            }

            start_recording(app, state).await?;
        }
        RecordingState::Recording | RecordingState::Processing => {
            // 当前录音中，停止录音
            info!("Current recording, stopping");

            stop_recording(state).await?;

            // 隐藏悬浮窗
            if let Some(overlay) = app.get_webview_window("overlay") {
                let _ = overlay.hide();
            }
        }
    }

    Ok(())
}

/// 获取音频设备列表
#[command]
pub async fn list_audio_devices() -> Result<Vec<String>, String> {
    debug!("Listing audio devices");
    use crate::audio::AudioCapture;

    AudioCapture::list_devices().map_err(|e| e.to_string())
}

/// 获取黑名单应用列表
#[command]
pub async fn get_blacklist() -> Result<Vec<String>, String> {
    use crate::system::WindowTracker;
    Ok(WindowTracker::get_blacklist())
}

/// 测试文本注入
#[command]
pub async fn test_injection(app: AppHandle, text: String) -> Result<(), String> {
    info!("Testing injection: {} chars", text.len());

    use crate::system::WindowTracker;

    // 获取当前活跃窗口
    let window = WindowTracker::get_current_window().map_err(|e| {
        error!("Failed to get current window: {}", e);
        e.to_string()
    })?;

    info!("Target window: {} - {}", window.app_name, window.title);

    // 检查是否为黑名单应用
    if window.is_blacklisted() {
        warn!("Target window is blacklisted: {}", window.app_name);
        return Err(format!("黑名单应用: {}", window.app_name));
    }

    // 在单独的线程中执行注入（因为 Enigo 不是 Send）
    let app_clone = app.clone();
    let text_clone = text.clone();
    let window_clone = window.clone();

    tokio::task::spawn_blocking(move || {
        use crate::input::{InjectionConfig, TextInjector};

        // 创建注入器
        let mut injector = TextInjector::with_config(app_clone.clone(), InjectionConfig::default())
            .map_err(|e| {
                error!("Failed to create injector: {}", e);
                e.to_string()
            })?;

        // 由于 inject 是 async，需要在 runtime 中运行
        let runtime = tokio::runtime::Handle::current();
        runtime.block_on(async {
            injector
                .inject(&text_clone, &window_clone)
                .await
                .map_err(|e| {
                    error!("Injection failed: {}", e);
                    e.to_string()
                })
        })?;

        info!("Injection successful");
        Ok::<(), String>(())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_default() {
        let config = Config::default();
        assert_eq!(config.language, "zh");
        assert_eq!(config.keyboard_max_chars, 10);
        assert!(config.enable_blacklist);
    }

    #[test]
    fn test_config_serialization() {
        let config = Config {
            api_key: "test-key".to_string(),
            hotkey: "Cmd+Shift+\\".to_string(),
            language: "en".to_string(),
            keyboard_max_chars: 20,
            enable_blacklist: false,
        };

        let json = serde_json::to_string(&config).unwrap();
        let deserialized: Config = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.api_key, config.api_key);
        assert_eq!(deserialized.language, config.language);
        assert_eq!(deserialized.keyboard_max_chars, 20);
    }

    #[tokio::test]
    async fn test_list_audio_devices() {
        let devices = list_audio_devices().await;
        // 可能成功也可能失败（取决于环境）
        println!("Audio devices result: {:?}", devices);
    }

    #[tokio::test]
    async fn test_get_blacklist() {
        let blacklist = get_blacklist().await.unwrap();
        assert!(!blacklist.is_empty());
        assert!(blacklist.contains(&"1Password".to_string()));
    }
}
