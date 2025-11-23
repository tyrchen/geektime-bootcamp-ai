pub mod audio;
mod commands;
pub mod network;
mod state;

use anyhow::Result;
use tauri::Manager;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

pub use state::AppState;

const APP_PATH: &str = "raflow";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() -> Result<()> {
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

    let state = AppState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![commands::greet,])
        .setup(|app| {
            app.manage(state);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");

    Ok(())
}
