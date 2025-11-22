mod commands;
mod state;

use anyhow::Result;
use tauri::Manager;

pub use state::AppState;

const APP_PATH: &str = "example-app";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() -> Result<()> {
    let app_path = dirs::data_local_dir().unwrap().join(APP_PATH);
    if !app_path.exists() {
        std::fs::create_dir_all(&app_path)?;
    }
    let state = AppState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(
            tauri_plugin_log::Builder::new()
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::Stdout,
                ))
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::LogDir {
                        file_name: Some("access.log".to_string()),
                    },
                ))
                .build(),
        )
        .invoke_handler(tauri::generate_handler![
            // Add new commands here
            commands::greet,
        ])
        .setup(|app| {
            app.manage(state);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");

    Ok(())
}
