//! 系统托盘模块
//!
//! 创建和管理系统托盘图标和菜单

use tauri::{
    AppHandle, Manager, Runtime,
    menu::{Menu, MenuItemBuilder, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use tracing::{debug, error};

/// 设置系统托盘
///
/// # Arguments
/// * `app` - Tauri AppHandle
///
/// # Example
/// ```no_run
/// use raflow_lib::system::setup_tray;
///
/// fn setup(app: &tauri::AppHandle) {
///     setup_tray(app).unwrap();
/// }
/// ```
pub fn setup_tray<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    debug!("Setting up system tray");

    // 创建菜单项
    let settings_item = MenuItemBuilder::with_id("settings", "设置").build(app)?;
    let separator = PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItemBuilder::with_id("quit", "退出 RAFlow").build(app)?;

    // 创建菜单
    let menu = Menu::with_items(app, &[&settings_item, &separator, &quit_item])?;

    // 创建托盘图标
    let _tray = TrayIconBuilder::new()
        .menu(&menu)
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("RAFlow - 实时语音听写")
        .on_menu_event(move |app, event| {
            debug!("Tray menu event: {:?}", event.id());

            match event.id().as_ref() {
                "settings" => {
                    // 显示设置窗口
                    if let Some(window) = app.get_webview_window("main") {
                        if let Err(e) = window.show() {
                            error!("Failed to show settings window: {}", e);
                        }
                        if let Err(e) = window.set_focus() {
                            error!("Failed to focus settings window: {}", e);
                        }
                    }
                }
                "quit" => {
                    debug!("Quit requested from tray");
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            match event {
                TrayIconEvent::Click {
                    button,
                    button_state,
                    ..
                } => {
                    if button == MouseButton::Left && button_state == MouseButtonState::Up {
                        // 左键单击 - 显示设置
                        debug!("Tray icon left clicked");
                        if let Some(app) = tray.app_handle().get_webview_window("main") {
                            let _ = app.show();
                            let _ = app.set_focus();
                        }
                    }
                }
                TrayIconEvent::DoubleClick { .. } => {
                    debug!("Tray icon double clicked");
                }
                _ => {}
            }
        })
        .build(app)?;

    debug!("System tray setup completed");

    Ok(())
}

#[cfg(test)]
mod tests {
    // 托盘测试需要完整的 Tauri 运行时
    // 应该在集成测试或 E2E 测试中进行
}
