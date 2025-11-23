//! ElevenLabs Scribe v2 WebSocket 协议定义
//!
//! 定义客户端和服务器之间的消息格式

use base64::{Engine as _, engine::general_purpose};
use serde::{Deserialize, Serialize};

/// 客户端发送的消息类型
#[derive(Debug, Serialize, Clone)]
#[serde(tag = "message_type")]
pub enum ClientMessage {
    /// 音频数据块
    #[serde(rename = "input_audio_chunk")]
    AudioChunk {
        /// Base64 编码的 PCM 音频数据（i16 小端格式）
        audio_base_64: String,
        /// 是否提交当前段落（触发 committed_transcript）
        #[serde(skip_serializing_if = "Option::is_none")]
        commit: Option<bool>,
    },
}

impl ClientMessage {
    /// 从 PCM i16 数据创建音频块消息
    ///
    /// # Arguments
    /// * `pcm_data` - i16 格式的 PCM 音频数据
    ///
    /// # Returns
    /// * `ClientMessage::AudioChunk` - 包含 Base64 编码音频的消息
    ///
    /// # Example
    /// ```
    /// use raflow_lib::network::ClientMessage;
    ///
    /// let pcm_data = vec![0i16, 100, -100, 200];
    /// let message = ClientMessage::audio_chunk(&pcm_data);
    /// ```
    pub fn audio_chunk(pcm_data: &[i16]) -> Self {
        // 将 i16 转换为字节（小端序）
        let bytes: Vec<u8> = pcm_data
            .iter()
            .flat_map(|&sample| sample.to_le_bytes())
            .collect();

        // Base64 编码
        let audio_base_64 = general_purpose::STANDARD.encode(bytes);

        Self::AudioChunk {
            audio_base_64,
            commit: None,
        }
    }

    /// 创建提交消息（触发 committed_transcript）
    ///
    /// 发送空音频块并设置 commit=true，通知服务器当前语音段落结束
    pub fn commit() -> Self {
        Self::AudioChunk {
            audio_base_64: String::new(),
            commit: Some(true),
        }
    }

    /// 序列化为 JSON 字符串
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }
}

/// 服务器发送的消息类型
#[derive(Debug, Deserialize, Clone, PartialEq)]
#[serde(tag = "message_type")]
pub enum ServerMessage {
    /// 会话开始
    #[serde(rename = "session_started")]
    SessionStarted {
        /// 会话 ID
        session_id: String,
        /// 配置信息
        #[serde(default)]
        config: serde_json::Value,
    },

    /// 部分转写结果（用户说话中）
    #[serde(rename = "partial_transcript")]
    PartialTranscript {
        /// 转写文本
        text: String,
        /// 创建时间戳（毫秒，可选）
        #[serde(default)]
        created_at_ms: Option<u64>,
    },

    /// 最终转写结果（已定稿）
    #[serde(rename = "committed_transcript")]
    CommittedTranscript {
        /// 转写文本
        text: String,
        /// 置信度（0.0 - 1.0，可选）
        #[serde(default)]
        confidence: Option<f32>,
    },

    /// 输入错误
    #[serde(rename = "input_error")]
    InputError {
        /// 错误消息
        error_message: String,
    },

    /// 会话结束
    #[serde(rename = "session_ended")]
    SessionEnded {
        /// 结束原因
        #[serde(default)]
        reason: String,
    },

    /// 认证错误
    #[serde(rename = "auth_error")]
    AuthError {
        /// 错误消息
        error: String,
    },

    /// 提交限制（音频时长不足）
    #[serde(rename = "commit_throttled")]
    CommitThrottled {
        /// 错误消息
        error: String,
    },
}

impl ServerMessage {
    /// 从 JSON 字符串解析服务器消息
    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }

    /// 检查是否为错误消息
    pub fn is_error(&self) -> bool {
        matches!(
            self,
            ServerMessage::InputError { .. } | ServerMessage::AuthError { .. }
        )
    }

    /// 检查是否为警告消息（非致命错误）
    pub fn is_warning(&self) -> bool {
        matches!(self, ServerMessage::CommitThrottled { .. })
    }

    /// 检查是否为转写消息
    pub fn is_transcript(&self) -> bool {
        matches!(
            self,
            ServerMessage::PartialTranscript { .. } | ServerMessage::CommittedTranscript { .. }
        )
    }

    /// 获取文本内容（如果是转写消息）
    pub fn text(&self) -> Option<&str> {
        match self {
            ServerMessage::PartialTranscript { text, .. } => Some(text),
            ServerMessage::CommittedTranscript { text, .. } => Some(text),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audio_chunk_creation() {
        let pcm_data = vec![0i16, 100, -100, 200, -200];
        let message = ClientMessage::audio_chunk(&pcm_data);

        match message {
            ClientMessage::AudioChunk { audio_base_64 } => {
                // 验证 Base64 编码正确
                let decoded = general_purpose::STANDARD.decode(&audio_base_64).unwrap();
                assert_eq!(decoded.len(), pcm_data.len() * 2); // 每个 i16 占 2 字节
            }
        }
    }

    #[test]
    fn test_client_message_serialization() {
        let pcm_data = vec![100i16, -100, 200];
        let message = ClientMessage::audio_chunk(&pcm_data);
        let json = message.to_json().unwrap();

        assert!(json.contains("input_audio_chunk"));
        assert!(json.contains("audio_base_64"));
    }

    #[test]
    fn test_session_started_deserialization() {
        let json = r#"{
            "message_type": "session_started",
            "session_id": "test-session-123",
            "config": {}
        }"#;

        let message = ServerMessage::from_json(json).unwrap();
        match message {
            ServerMessage::SessionStarted { session_id, .. } => {
                assert_eq!(session_id, "test-session-123");
            }
            _ => panic!("Expected SessionStarted"),
        }
    }

    #[test]
    fn test_partial_transcript_deserialization() {
        let json = r#"{
            "message_type": "partial_transcript",
            "text": "hello world",
            "created_at_ms": 1234567890
        }"#;

        let message = ServerMessage::from_json(json).unwrap();
        assert!(message.is_transcript());
        assert_eq!(message.text(), Some("hello world"));

        match message {
            ServerMessage::PartialTranscript {
                text,
                created_at_ms,
            } => {
                assert_eq!(text, "hello world");
                assert_eq!(created_at_ms, Some(1234567890));
            }
            _ => panic!("Expected PartialTranscript"),
        }
    }

    #[test]
    fn test_committed_transcript_deserialization() {
        let json = r#"{
            "message_type": "committed_transcript",
            "text": "final text",
            "confidence": 0.98
        }"#;

        let message = ServerMessage::from_json(json).unwrap();
        assert!(message.is_transcript());
        assert_eq!(message.text(), Some("final text"));

        match message {
            ServerMessage::CommittedTranscript { text, confidence } => {
                assert_eq!(text, "final text");
                assert!((confidence.unwrap() - 0.98).abs() < 0.01);
            }
            _ => panic!("Expected CommittedTranscript"),
        }
    }

    #[test]
    fn test_input_error_deserialization() {
        let json = r#"{
            "message_type": "input_error",
            "error_message": "Invalid audio format"
        }"#;

        let message = ServerMessage::from_json(json).unwrap();
        assert!(message.is_error());

        match message {
            ServerMessage::InputError { error_message } => {
                assert_eq!(error_message, "Invalid audio format");
            }
            _ => panic!("Expected InputError"),
        }
    }

    #[test]
    fn test_session_ended_deserialization() {
        let json = r#"{
            "message_type": "session_ended",
            "reason": "timeout"
        }"#;

        let message = ServerMessage::from_json(json).unwrap();
        match message {
            ServerMessage::SessionEnded { reason } => {
                assert_eq!(reason, "timeout");
            }
            _ => panic!("Expected SessionEnded"),
        }
    }
}
