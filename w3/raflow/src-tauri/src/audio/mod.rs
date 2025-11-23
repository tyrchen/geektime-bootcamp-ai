//! 音频处理模块
//!
//! 包含音频采集、缓冲、重采样、噪声抑制等功能

mod buffer;
mod capture;
mod processor;
mod resampler;

pub use buffer::RingBuffer;
pub use capture::{AudioCapture, CaptureError};
pub use processor::{AudioProcessor, AudioProcessorConfig, NoiseSuppressionLevel, ProcessorError};
pub use resampler::{AudioResampler, Quality, ResamplerError};

use tokio::sync::mpsc;
use tracing::{trace, debug, error, info};

/// 音频管理器
///
/// 整合音频采集、缓冲、重采样和噪声抑制功能，提供统一的音频处理接口
pub struct AudioManager {
    capture: AudioCapture,
    buffer: RingBuffer,
    output_tx: mpsc::Sender<Vec<i16>>,
    enable_noise_suppression: bool,
    noise_suppression_level: NoiseSuppressionLevel,
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
        // 默认启用降噪（但会根据采样率自动决定是否实际使用）
        Self::with_noise_suppression(output_tx, true, NoiseSuppressionLevel::default())
    }

    /// 创建新的音频管理器（带噪声抑制配置）
    ///
    /// # Arguments
    /// * `output_tx` - 用于发送处理后音频数据的通道
    /// * `enable_noise_suppression` - 是否启用噪声抑制
    /// * `noise_suppression_level` - 噪声抑制级别
    pub fn with_noise_suppression(
        output_tx: mpsc::Sender<Vec<i16>>,
        enable_noise_suppression: bool,
        noise_suppression_level: NoiseSuppressionLevel,
    ) -> Result<Self, CaptureError> {
        let capture = AudioCapture::new()?;
        let sample_rate = capture.sample_rate();

        info!("Device sample rate: {}Hz", sample_rate);
        info!(
            "Noise suppression: enabled={}, level={:?}",
            enable_noise_suppression, noise_suppression_level
        );

        // 创建环形缓冲区：200 个块（约 4 秒缓冲），每块最大 2048 帧
        let buffer = RingBuffer::new(200, 2048);

        Ok(Self {
            capture,
            buffer,
            output_tx,
            enable_noise_suppression,
            noise_suppression_level,
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
        self.spawn_consumer_task(sample_rate, self.enable_noise_suppression, self.noise_suppression_level);

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
    /// 从缓冲区读取音频数据，进行重采样、噪声抑制和量化，然后发送到输出通道
    fn spawn_consumer_task(&self, sample_rate: u32, enable_noise_suppression: bool, _noise_level: NoiseSuppressionLevel) {
        let buffer = self.buffer.clone();
        let output_tx = self.output_tx.clone();

        tokio::spawn(async move {
            info!("Audio consumer task started");

            // 使用 Low 质量（最快初始化，够用）
            let mut resampler: Option<AudioResampler> = None;
            let mut last_chunk_size = 0usize;

            // 创建噪声抑制处理器（如果启用）
            // 注意：RNNoise 严格要求 48kHz 采样率，音频已在 AudioCapture 中转换为单声道
            let mut noise_processor: Option<AudioProcessor> = if enable_noise_suppression {
                // 检查设备采样率
                if sample_rate == 48000 {
                    info!("Noise suppression processor initialized (48kHz, mono)");
                    Some(AudioProcessor::new())
                } else {
                    info!("Noise suppression disabled: device sample rate is {}Hz, RNNoise requires 48kHz", sample_rate);
                    None
                }
            } else {
                info!("Noise suppression disabled by configuration");
                None
            };

            // 静音检测状态
            let mut silence_chunks = 0usize; // 连续静音的块数
            let silence_threshold = 6; // 连续 6 个块（约 3 秒）认为是持续静音，避免吞掉尾音

            loop {
                if let Some(audio_chunk) = buffer.pop() {
                    let chunk_len = audio_chunk.len();

                    // 只在块大小变化时重新创建
                    if chunk_len != last_chunk_size {
                        info!("Creating resampler for chunk size: {} (was: {})", chunk_len, last_chunk_size);

                        let start = std::time::Instant::now();

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

                    // 应用噪声抑制（在重采样前，因为 RNNoise 需要 48kHz）
                    let mut processed_chunk = audio_chunk.clone();
                    let mut is_silence = false;

                    if let Some(ref mut processor) = noise_processor {
                        let frame_size = processor.frame_size();
                        let mut temp_output = Vec::with_capacity(audio_chunk.len());
                        let mut vad_sum = 0.0f32;
                        let mut vad_count = 0;

                        for chunk in audio_chunk.chunks(frame_size) {
                            if chunk.len() == frame_size {
                                match processor.process(chunk) {
                                    Ok((processed_frame, vad_prob)) => {
                                        temp_output.extend_from_slice(&processed_frame);
                                        vad_sum += vad_prob;
                                        vad_count += 1;
                                    }
                                    Err(e) => {
                                        error!("Noise suppression error: {}", e);
                                        temp_output.extend_from_slice(chunk);
                                    }
                                }
                            } else {
                                temp_output.extend_from_slice(chunk);
                            }
                        }

                        processed_chunk = temp_output;

                        // 静音检测：VAD + 能量双重检测
                        if vad_count > 0 {
                            let avg_vad = vad_sum / vad_count as f32;
                            let energy: f32 = processed_chunk.iter().map(|&x| x * x).sum::<f32>() / processed_chunk.len() as f32;

                            // 静音判断：VAD < 0.05 且 能量 < 0.00005（更宽松的阈值，避免吞字）
                            is_silence = avg_vad < 0.05 && energy < 0.00005;

                            if is_silence {
                                trace!("Silence detected: VAD={:.3}, Energy={:.6}", avg_vad, energy);
                            }
                        }
                    } else {
                        // 没有降噪时，只用能量检测（更低的阈值）
                        let energy: f32 = audio_chunk.iter().map(|&x| x * x).sum::<f32>() / audio_chunk.len() as f32;
                        is_silence = energy < 0.00005;
                    }

                    // 更新静音计数器
                    if is_silence {
                        silence_chunks += 1;
                        if silence_chunks == silence_threshold {
                            info!("Continuous silence detected ({} chunks, ~3s), will stop sending if continues", silence_chunks);
                        }
                    } else {
                        if silence_chunks > 0 {
                            debug!("Voice detected, resetting silence counter (was {})", silence_chunks);
                        }
                        silence_chunks = 0;
                    }

                    // 如果连续静音超过阈值，跳过发送（但继续处理，保持流畅）
                    if silence_chunks >= silence_threshold {
                        buffer.recycle(audio_chunk);
                        continue;
                    }

                    // 重采样
                    if let Some(ref mut r) = resampler {
                        match r.process(&processed_chunk) {
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
