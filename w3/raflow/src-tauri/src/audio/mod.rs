//! 音频处理模块
//!
//! 包含音频采集、缓冲、重采样等功能

mod buffer;
mod capture;
mod resampler;

pub use buffer::RingBuffer;
pub use capture::{AudioCapture, CaptureError};
pub use resampler::{AudioResampler, Quality, ResamplerError};

use tokio::sync::mpsc;
use tracing::{debug, error, info};

/// 音频管理器
///
/// 整合音频采集、缓冲和重采样功能，提供统一的音频处理接口
pub struct AudioManager {
    capture: AudioCapture,
    buffer: RingBuffer,
    output_tx: mpsc::Sender<Vec<i16>>,
}

impl AudioManager {
    /// 创建新的音频管理器
    ///
    /// # Arguments
    /// * `output_tx` - 用于发送处理后音频数据的通道
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::audio::AudioManager;
    /// use tokio::sync::mpsc;
    ///
    /// #[tokio::main]
    /// async fn main() {
    ///     let (tx, mut rx) = mpsc::channel(100);
    ///     let manager = AudioManager::new(tx).unwrap();
    ///
    ///     // 接收处理后的音频数据
    ///     tokio::spawn(async move {
    ///         while let Some(audio_data) = rx.recv().await {
    ///             println!("Received {} samples", audio_data.len());
    ///         }
    ///     });
    /// }
    /// ```
    pub fn new(output_tx: mpsc::Sender<Vec<i16>>) -> Result<Self, CaptureError> {
        let capture = AudioCapture::new()?;
        let sample_rate = capture.sample_rate();

        info!("Device sample rate: {}Hz", sample_rate);

        // 创建环形缓冲区：200 个块（约 4 秒缓冲），每块最大 2048 帧
        let buffer = RingBuffer::new(200, 2048);

        Ok(Self {
            capture,
            buffer,
            output_tx,
        })
    }

    /// 启动音频处理
    ///
    /// 启动音频采集并创建消费者任务处理音频数据
    pub fn start(&mut self) -> Result<(), CaptureError> {
        let buffer = self.buffer.clone();
        let sample_rate = self.capture.sample_rate();

        info!("Starting audio capture at {}Hz", sample_rate);

        // 启动音频采集
        self.capture.start(move |data| {
            if !buffer.push(data) {
                debug!("Audio buffer full, dropping samples");
            }
        })?;

        // 启动消费者任务
        self.spawn_consumer_task(sample_rate);

        Ok(())
    }

    /// 停止音频处理
    pub fn stop(&mut self) {
        self.capture.stop();
        info!("Audio capture stopped");
    }

    /// 获取当前采样率
    pub fn sample_rate(&self) -> u32 {
        self.capture.sample_rate()
    }

    /// 获取缓冲区状态
    pub fn buffer_status(&self) -> (usize, usize) {
        (self.buffer.len(), self.buffer.capacity())
    }

    /// 生成消费者任务
    ///
    /// 从缓冲区读取音频数据，进行重采样和量化，然后发送到输出通道
    fn spawn_consumer_task(&self, sample_rate: u32) {
        let buffer = self.buffer.clone();
        let output_tx = self.output_tx.clone();

        tokio::spawn(async move {
            info!("Audio consumer task started");

            // 使用 Medium 质量以提高处理速度（High 质量初始化太慢）
            // 第一次初始化使用最大可能块大小
            let mut resampler: Option<AudioResampler> = None;
            let mut last_chunk_size = 0usize;

            loop {
                if let Some(audio_chunk) = buffer.pop() {
                    let chunk_len = audio_chunk.len();

                    // 只在块大小变化时重新创建
                    if chunk_len != last_chunk_size {
                        info!("Creating resampler for chunk size: {} (was: {})", chunk_len, last_chunk_size);

                        let start = std::time::Instant::now();

                        // 使用 Low 质量（最快初始化，够用）
                        resampler = match AudioResampler::new(sample_rate, 16000, chunk_len, 1, Quality::Low)
                        {
                            Ok(r) => {
                                last_chunk_size = chunk_len;
                                info!("Resampler created in {:?}", start.elapsed());
                                Some(r)
                            },
                            Err(e) => {
                                error!("Failed to create resampler: {}", e);
                                buffer.recycle(audio_chunk);
                                continue;
                            }
                        };
                    }

                    // 重采样
                    if let Some(ref mut r) = resampler {
                        match r.process(&audio_chunk) {
                            Ok(resampled) => {
                                // 量化为 i16
                                let i16_samples = AudioResampler::quantize_to_i16(&resampled);

                                // 发送到网络模块
                                if output_tx.send(i16_samples).await.is_err() {
                                    error!("Output channel closed, stopping consumer");
                                    break;
                                }
                            }
                            Err(e) => {
                                error!("Resampling error: {}", e);
                            }
                        }
                    }

                    // 回收缓冲区
                    buffer.recycle(audio_chunk);
                } else {
                    // 缓冲区为空，短暂休眠
                    tokio::time::sleep(tokio::time::Duration::from_millis(1)).await;
                }
            }

            info!("Audio consumer task stopped");
        });
    }
}

impl Drop for AudioManager {
    fn drop(&mut self) {
        self.stop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_audio_manager_creation() {
        let (tx, _rx) = mpsc::channel(100);
        let manager = AudioManager::new(tx);
        assert!(manager.is_ok());
    }

    #[tokio::test]
    #[ignore] // 需要实际音频设备
    async fn test_audio_manager_start_stop() {
        let (tx, mut rx) = mpsc::channel(100);
        let mut manager = AudioManager::new(tx).unwrap();

        // 启动音频处理
        manager.start().unwrap();

        // 接收一些数据
        tokio::time::timeout(tokio::time::Duration::from_secs(1), async {
            let mut count = 0;
            while let Some(data) = rx.recv().await {
                count += 1;
                println!("Received chunk {}: {} samples", count, data.len());
                if count >= 5 {
                    break;
                }
            }
        })
        .await
        .ok();

        // 停止
        manager.stop();
    }

    #[test]
    fn test_buffer_status() {
        let (tx, _rx) = mpsc::channel(100);
        let manager = AudioManager::new(tx).unwrap();
        let (len, cap) = manager.buffer_status();
        assert_eq!(len, 0);
        assert_eq!(cap, 200); // 更新为新的容量
    }
}
