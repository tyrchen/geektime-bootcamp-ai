// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use anyhow::Result;

fn main() -> Result<()> {
    // 安装 rustls 的默认 crypto provider
    let _ = rustls::crypto::aws_lc_rs::default_provider().install_default();

    raflow_lib::run()?;
    Ok(())
}
