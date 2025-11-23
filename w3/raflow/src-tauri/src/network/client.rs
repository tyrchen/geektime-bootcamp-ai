//! WebSocket 客户端模块
//!
//! 实现与 ElevenLabs Scribe v2 API 的 WebSocket 连接

use futures_util::{StreamExt, stream::SplitSink, stream::SplitStream};
use thiserror::Error;
use tokio::net::TcpStream;
use tokio_tungstenite::{
    connect_async,
    tungstenite::{client::IntoClientRequest, Message},
    MaybeTlsStream, WebSocketStream,
};
use tracing::{debug, info};

#[derive(Error, Debug)]
pub enum ClientError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),

    #[error("WebSocket error: {0}")]
    WebSocketError(#[from] tokio_tungstenite::tungstenite::Error),

    #[error("Invalid URL: {0}")]
    InvalidUrl(String),

    #[error("Authentication failed: {0}")]
    AuthenticationFailed(String),
}

type Result<T> = std::result::Result<T, ClientError>;

/// WebSocket 发送端类型别名
pub type WsSink = SplitSink<WebSocketStream<MaybeTlsStream<TcpStream>>, Message>;

/// WebSocket 接收端类型别名
pub type WsStream = SplitStream<WebSocketStream<MaybeTlsStream<TcpStream>>>;

/// Scribe v2 客户端配置
#[derive(Debug, Clone)]
pub struct ClientConfig {
    /// API Key
    pub api_key: String,
    /// 模型 ID
    pub model_id: String,
    /// 语言代码
    pub language_code: String,
    /// 编码格式
    pub encoding: String,
}

impl Default for ClientConfig {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            model_id: "scribe_v2_realtime".to_string(),
            language_code: "cmn".to_string(), // 使用 ISO 639-3 普通话代码
            encoding: "pcm_16000".to_string(),
        }
    }
}

/// ElevenLabs Scribe v2 WebSocket 客户端
pub struct ScribeClient {
    config: ClientConfig,
    base_url: String,
}

impl ScribeClient {
    /// 创建新的客户端
    ///
    /// # Arguments
    /// * `api_key` - ElevenLabs API Key
    ///
    /// # Example
    /// ```
    /// use raflow_lib::network::ScribeClient;
    ///
    /// let client = ScribeClient::new("your-api-key".to_string());
    /// ```
    pub fn new(api_key: String) -> Self {
        Self::with_config(ClientConfig {
            api_key,
            ..Default::default()
        })
    }

    /// 使用自定义配置创建客户端
    pub fn with_config(config: ClientConfig) -> Self {
        Self {
            config,
            base_url: "wss://api.elevenlabs.io/v1/speech-to-text/realtime".to_string(),
        }
    }

    /// 建立 WebSocket 连接
    ///
    /// # Returns
    /// * `Ok((WsSink, WsStream))` - 成功返回发送和接收端
    /// * `Err(ClientError)` - 连接失败
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::network::ScribeClient;
    ///
    /// #[tokio::main]
    /// async fn main() {
    ///     let client = ScribeClient::new("your-api-key".to_string());
    ///     let (sink, stream) = client.connect().await.unwrap();
    /// }
    /// ```
    pub async fn connect(&self) -> Result<(WsSink, WsStream)> {
        // 构建 URL
        let url = format!(
            "{}?model_id={}&encoding={}",
            self.base_url, self.config.model_id, self.config.encoding
        );

        debug!("Connecting to: {}", url);

        // 使用 IntoClientRequest trait 添加自定义 header
        let mut request = url.into_client_request()
            .map_err(|e| ClientError::InvalidUrl(e.to_string()))?;

        // 添加 API Key header
        request.headers_mut()
            .insert("xi-api-key", self.config.api_key.parse()
                .map_err(|_| ClientError::AuthenticationFailed("Invalid API key format".to_string()))?);

        debug!("Request headers: {:?}", request.headers());

        // 连接
        let (ws_stream, response) = connect_async(request)
            .await
            .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;

        info!("WebSocket connected: status = {}", response.status());

        // 分离发送和接收端
        let (sink, stream) = ws_stream.split();

        Ok((sink, stream))
    }

    /// 设置语言代码
    pub fn set_language(&mut self, language_code: String) {
        self.config.language_code = language_code;
    }

    /// 获取当前配置
    pub fn config(&self) -> &ClientConfig {
        &self.config
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = ScribeClient::new("test-api-key".to_string());
        assert_eq!(client.config.api_key, "test-api-key");
        assert_eq!(client.config.model_id, "scribe_v2_realtime");
    }

    #[test]
    fn test_custom_config() {
        let config = ClientConfig {
            api_key: "custom-key".to_string(),
            model_id: "custom-model".to_string(),
            language_code: "en".to_string(),
            encoding: "pcm_8000".to_string(),
        };

        let client = ScribeClient::with_config(config);
        assert_eq!(client.config.language_code, "en");
        assert_eq!(client.config.encoding, "pcm_8000");
    }

    #[test]
    fn test_set_language() {
        let mut client = ScribeClient::new("test-key".to_string());
        client.set_language("fr".to_string());
        assert_eq!(client.config.language_code, "fr");
    }

    // 集成测试需要真实的 API Key
    #[tokio::test]
    #[ignore]
    async fn test_real_connection() {
        let api_key = std::env::var("ELEVENLABS_API_KEY").expect("ELEVENLABS_API_KEY not set");

        let client = ScribeClient::new(api_key);
        let result = client.connect().await;

        assert!(result.is_ok());
    }
}
