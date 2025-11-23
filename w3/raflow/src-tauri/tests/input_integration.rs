//! 输入模块集成测试
//!
//! 测试窗口追踪和文本注入的完整流程

use raflow_lib::input::{InjectionConfig, InjectionStrategy};
use raflow_lib::system::{WindowInfo, WindowTracker};

#[test]
fn test_window_info_serialization() {
    let window = WindowInfo {
        app_name: "Google Chrome".to_string(),
        title: "GitHub".to_string(),
        process_id: 12345,
        position: (100, 100, 1920, 1080),
    };

    // 测试序列化
    let json = serde_json::to_string(&window).unwrap();
    assert!(json.contains("Google Chrome"));

    // 测试反序列化
    let deserialized: WindowInfo = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized, window);
}

#[test]
fn test_blacklist_detection() {
    // 密码管理器应该被检测为黑名单
    let password_managers = vec![
        "1Password",
        "Bitwarden",
        "Keychain Access",
        "LastPass",
        "KeePass",
        "Dashlane",
    ];

    for app in password_managers {
        let window = WindowInfo {
            app_name: app.to_string(),
            title: "Test".to_string(),
            process_id: 12345,
            position: (0, 0, 800, 600),
        };

        assert!(
            WindowTracker::is_blacklisted(&window),
            "{} should be blacklisted",
            app
        );
    }

    // 普通应用不应该被黑名单
    let normal_apps = vec![
        "Google Chrome",
        "Safari",
        "Firefox",
        "Microsoft Word",
        "Visual Studio Code",
        "Slack",
    ];

    for app in normal_apps {
        let window = WindowInfo {
            app_name: app.to_string(),
            title: "Test".to_string(),
            process_id: 12345,
            position: (0, 0, 1920, 1080),
        };

        assert!(
            !WindowTracker::is_blacklisted(&window),
            "{} should not be blacklisted",
            app
        );
    }
}

#[test]
fn test_terminal_detection() {
    let terminals = vec!["Terminal", "iTerm2", "Alacritty", "Kitty", "WezTerm"];

    for term in terminals {
        let window = WindowInfo {
            app_name: term.to_string(),
            title: "bash".to_string(),
            process_id: 12345,
            position: (0, 0, 800, 600),
        };

        assert!(
            WindowTracker::is_terminal(&window),
            "{} should be detected as terminal",
            term
        );
    }
}

#[test]
fn test_injection_strategy_selection() {
    let config = InjectionConfig::default();

    // 短文本应该使用键盘
    let short_text = "Hello";
    let strategy = if short_text.len() <= config.keyboard_max_chars {
        InjectionStrategy::Keyboard
    } else {
        InjectionStrategy::Clipboard
    };
    assert_eq!(strategy, InjectionStrategy::Keyboard);

    // 长文本应该使用剪贴板
    let long_text = "This is a very long text that should definitely use clipboard strategy";
    let strategy = if long_text.len() <= config.keyboard_max_chars {
        InjectionStrategy::Keyboard
    } else {
        InjectionStrategy::Clipboard
    };
    assert_eq!(strategy, InjectionStrategy::Clipboard);
}

#[test]
fn test_injection_config_validation() {
    let mut config = InjectionConfig::default();

    // 测试默认值
    assert_eq!(config.keyboard_max_chars, 10);
    assert_eq!(config.typing_delay_ms, 5);
    assert_eq!(config.focus_wait_ms, 50);
    assert!(config.enable_blacklist);
    assert_eq!(config.max_text_length, 10000);

    // 测试修改
    config.keyboard_max_chars = 20;
    config.enable_blacklist = false;

    assert_eq!(config.keyboard_max_chars, 20);
    assert!(!config.enable_blacklist);
}

#[test]
fn test_text_length_limits() {
    let config = InjectionConfig::default();

    // 正常文本
    let normal_text = "Hello, world!";
    assert!(normal_text.len() <= config.max_text_length);

    // 超长文本（模拟）
    let too_long = "x".repeat(config.max_text_length + 1);
    assert!(too_long.len() > config.max_text_length);
}

#[test]
fn test_window_position_validation() {
    let window = WindowInfo {
        app_name: "Test App".to_string(),
        title: "Test Window".to_string(),
        process_id: 12345,
        position: (100, 200, 1920, 1080),
    };

    let (x, y, width, height) = window.position;
    assert_eq!(x, 100);
    assert_eq!(y, 200);
    assert_eq!(width, 1920);
    assert_eq!(height, 1080);
}

#[test]
#[ignore] // 需要 GUI 环境
fn test_get_current_window() {
    let window = WindowTracker::get_current_window();
    assert!(window.is_ok());

    let win = window.unwrap();
    println!("Current window: {} - {}", win.app_name, win.title);
    assert!(!win.app_name.is_empty());
    assert!(win.position.2 > 0); // width > 0
    assert!(win.position.3 > 0); // height > 0
}
