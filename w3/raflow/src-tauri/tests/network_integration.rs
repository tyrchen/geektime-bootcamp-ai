//! 网络模块集成测试
//!
//! 测试音频数据流到网络传输的完整流程

use raflow_lib::network::{ClientMessage, NetworkManager, ServerMessage};
use tokio::sync::mpsc;
use tokio::time::{Duration, timeout};

#[tokio::test]
async fn test_protocol_roundtrip() {
    // 测试协议消息的序列化和反序列化
    let pcm_data = vec![100i16, -100, 200, -200];
    let client_msg = ClientMessage::audio_chunk(&pcm_data);

    // 序列化
    let json = client_msg.to_json().unwrap();
    assert!(json.contains("input_audio_chunk"));
    assert!(json.contains("audio_base_64"));

    // 模拟服务器响应
    let server_json = r#"{
        "message_type": "partial_transcript",
        "text": "hello",
        "created_at_ms": 1234567890
    }"#;

    let server_msg = ServerMessage::from_json(server_json).unwrap();
    assert!(server_msg.is_transcript());
    assert_eq!(server_msg.text(), Some("hello"));
}

#[tokio::test]
async fn test_audio_to_network_pipeline() {
    // 创建通道
    let (audio_tx, audio_rx) = mpsc::channel::<Vec<i16>>(100);
    let (event_tx, mut event_rx) = mpsc::channel::<ServerMessage>(100);

    // 创建网络管理器（不启动实际连接）
    let _manager = NetworkManager::new("test-api-key".to_string(), audio_rx, event_tx);

    // 模拟发送音频数据
    tokio::spawn(async move {
        for i in 0..5 {
            let audio_chunk = vec![i as i16; 160]; // 10ms @ 16kHz
            if audio_tx.send(audio_chunk).await.is_err() {
                break;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    });

    // 验证通道工作正常（实际连接测试需要真实 API）
    drop(_manager);

    // 通道应该关闭
    let result = timeout(Duration::from_millis(100), event_rx.recv()).await;
    assert!(result.is_ok());
}

#[tokio::test]
async fn test_message_parsing_edge_cases() {
    // 测试各种边界情况

    // 空文本
    let json = r#"{
        "message_type": "partial_transcript",
        "text": "",
        "created_at_ms": 0
    }"#;
    let msg = ServerMessage::from_json(json).unwrap();
    assert_eq!(msg.text(), Some(""));

    // 包含特殊字符
    let json = r#"{
        "message_type": "committed_transcript",
        "text": "Hello, 世界! 🎉",
        "confidence": 0.95
    }"#;
    let msg = ServerMessage::from_json(json).unwrap();
    assert_eq!(msg.text(), Some("Hello, 世界! 🎉"));

    // 错误消息
    let json = r#"{
        "message_type": "input_error",
        "error_message": "Invalid sample rate"
    }"#;
    let msg = ServerMessage::from_json(json).unwrap();
    assert!(msg.is_error());
}

#[tokio::test]
async fn test_concurrent_audio_sending() {
    let (audio_tx, audio_rx) = mpsc::channel::<Vec<i16>>(100);
    let (event_tx, _event_rx) = mpsc::channel::<ServerMessage>(100);

    let _manager = NetworkManager::new("test-key".to_string(), audio_rx, event_tx);

    // 多个生产者并发发送
    let mut handles = vec![];
    for i in 0..3 {
        let tx = audio_tx.clone();
        let handle = tokio::spawn(async move {
            for j in 0..10 {
                let data = vec![(i * 100 + j) as i16; 160];
                if tx.send(data).await.is_err() {
                    break;
                }
            }
        });
        handles.push(handle);
    }

    // 等待所有生产者完成
    for handle in handles {
        handle.await.unwrap();
    }

    // 关闭发送端
    drop(audio_tx);
}

#[tokio::test]
#[ignore] // 需要真实的 ElevenLabs API Key
async fn test_real_websocket_connection() {
    let api_key = std::env::var("ELEVENLABS_API_KEY").expect("ELEVENLABS_API_KEY not set");

    let (_audio_tx, audio_rx) = mpsc::channel::<Vec<i16>>(100);
    let (event_tx, mut event_rx) = mpsc::channel::<ServerMessage>(100);

    let mut manager = NetworkManager::new(api_key, audio_rx, event_tx);

    // 启动管理器（在后台）
    let manager_handle = tokio::spawn(async move { manager.run().await });

    // 等待会话开始事件
    let result = timeout(Duration::from_secs(5), async {
        while let Some(msg) = event_rx.recv().await {
            if matches!(msg, ServerMessage::SessionStarted { .. }) {
                return true;
            }
        }
        false
    })
    .await;

    assert!(result.is_ok());
    assert!(result.unwrap());

    // 清理
    manager_handle.abort();
}
