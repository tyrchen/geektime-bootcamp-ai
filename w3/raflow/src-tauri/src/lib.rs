pub mod audio;
mod commands;
pub mod config;
pub mod core;
pub mod input;
pub mod network;
mod state;
pub mod system;

use anyhow::Result;
use tauri::Manager;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

pub use state::{AppState, RecordingState};

const APP_PATH: &str = "raflow";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() -> Result<()> {
    // 设置 panic hook 捕获崩溃信息
    std::panic::set_hook(Box::new(|panic_info| {
        eprintln!("=== PANIC ===");
        eprintln!("{}", panic_info);
        if let Some(location) = panic_info.location() {
            eprintln!("Location: {}:{}:{}", location.file(), location.line(), location.column());
        }
        if let Some(s) = panic_info.payload().downcast_ref::<&str>() {
            eprintln!("Panic message: {}", s);
        }
        eprintln!("=============");
    }));

    // 初始化 tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "raflow=debug,tokio=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let app_path = dirs::data_local_dir()
        .ok_or_else(|| anyhow::anyhow!("Failed to get data local dir"))?
        .join(APP_PATH);

    if !app_path.exists() {
        std::fs::create_dir_all(&app_path)?;
    }

    let (state, control_rx, state_tx) = AppState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            commands::get_config,
            commands::save_config,
            commands::start_recording,
            commands::stop_recording,
            commands::toggle_recording,
            commands::list_audio_devices,
            commands::get_blacklist,
            commands::test_injection,
        ])
        .setup(move |app| {
            use config::ConfigManager;
            use system::HotkeyManager;

            // 设置系统托盘
            system::setup_tray(app.handle())?;

            // 加载配置
            let config = ConfigManager::load(app.handle()).unwrap_or_default();

            // 注册全局热键
            if let Err(e) = HotkeyManager::register(app.handle(), &config.hotkey) {
                tracing::warn!("Failed to register hotkey: {}", e);
            }

            // 启动后台控制任务（使用 LocalSet 支持非 Send future）
            let app_handle = app.handle().clone();

            std::thread::spawn(move || {
                use crate::core::AppController;
                use crate::state::ControlCommand;

                let rt = tokio::runtime::Runtime::new().unwrap();

                rt.block_on(async move {
                    let mut controller: Option<AppController> = None;
                    let mut control_rx = control_rx;

                    while let Some(cmd) = control_rx.recv().await {
                        match cmd {
                            ControlCommand::Start { config, response } => {
                                tracing::info!("Control task: Start");

                                if controller.is_some() {
                                    let _ = response.send(Err("Already running".to_string()));
                                    continue;
                                }

                                let mut ctrl = AppController::new(app_handle.clone(), config);
                                match ctrl.start_recording().await {
                                    Ok(()) => {
                                        controller = Some(ctrl);
                                        let _ = response.send(Ok(()));
                                        let _ = state_tx.send(RecordingState::Recording);
                                    }
                                    Err(e) => {
                                        let _ = response.send(Err(e.to_string()));
                                    }
                                }
                            }

                            ControlCommand::Stop { response } => {
                                tracing::info!("Control task: Stop");

                                if let Some(mut ctrl) = controller.take() {
                                    match ctrl.stop_recording().await {
                                        Ok(()) => {
                                            let _ = response.send(Ok(()));
                                            let _ = state_tx.send(RecordingState::Idle);
                                        }
                                        Err(e) => {
                                            let _ = response.send(Err(e.to_string()));
                                        }
                                    }
                                } else {
                                    let _ = response.send(Ok(())); // 已停止
                                }
                            }
                        }
                    }

                    tracing::info!("Control task stopped");
                });
            });

            app.manage(state);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");

    Ok(())
}
