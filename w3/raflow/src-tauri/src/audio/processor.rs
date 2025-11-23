//! 音频降噪处理模块
//!
//! 使用 RNNoise 算法提供噪声抑制功能

use nnnoiseless::DenoiseState;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ProcessorError {
    #[error("Invalid frame size: expected {expected}, got {actual}")]
    InvalidFrameSize { expected: usize, actual: usize },

    #[error("Failed to process audio: {0}")]
    ProcessError(String),
}

type Result<T> = std::result::Result<T, ProcessorError>;

/// 噪声抑制处理器
///
/// 基于 RNNoise 算法的音频降噪处理器
pub struct AudioProcessor {
    denoiser: Box<DenoiseState<'static>>,
    frame_size: usize,
}

impl AudioProcessor {
    /// 创建新的音频处理器
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::audio::AudioProcessor;
    ///
    /// let processor = AudioProcessor::new();
    /// ```
    pub fn new() -> Self {
        let denoiser = DenoiseState::new();
        Self {
            denoiser,
            frame_size: DenoiseState::FRAME_SIZE,
        }
    }

    /// 处理音频帧
    ///
    /// # Arguments
    /// * `frame` - 输入音频帧（f32 格式，48kHz 采样率）
    ///
    /// # Returns
    /// 处理后的音频帧和语音活动概率（VAD）
    ///
    /// # Note
    /// RNNoise 期望 48kHz 采样率的音频输入，帧大小为 480 samples (10ms @ 48kHz)
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::audio::AudioProcessor;
    ///
    /// let mut processor = AudioProcessor::new();
    /// let audio_frame = vec![0.0f32; 480]; // 10ms @ 48kHz
    /// let (processed, vad_prob) = processor.process(&audio_frame).unwrap();
    /// ```
    pub fn process(&mut self, frame: &[f32]) -> Result<(Vec<f32>, f32)> {
        // 验证帧大小
        if frame.len() != self.frame_size {
            return Err(ProcessorError::InvalidFrameSize {
                expected: self.frame_size,
                actual: frame.len(),
            });
        }

        // 处理音频
        let mut output = vec![0.0f32; self.frame_size];
        let vad_prob = self.denoiser.process_frame(&mut output, frame);

        Ok((output, vad_prob))
    }

    /// 获取期望的帧大小（480 samples @ 48kHz = 10ms）
    pub fn frame_size(&self) -> usize {
        self.frame_size
    }
}

impl Default for AudioProcessor {
    fn default() -> Self {
        Self::new()
    }
}

/// 音频处理器配置（为了保持与之前 API 的兼容性）
#[derive(Debug, Clone)]
pub struct AudioProcessorConfig {
    /// 占位字段（RNNoise 不需要额外配置）
    _placeholder: (),
}

impl Default for AudioProcessorConfig {
    fn default() -> Self {
        Self { _placeholder: () }
    }
}

/// 噪声抑制级别（为了保持 API 兼容性，RNNoise 不支持级别调整）
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NoiseSuppressionLevel {
    /// 低级别（占位）
    Low,
    /// 中级别（占位）
    Moderate,
    /// 高级别（占位）
    High,
    /// 极高级别（占位）
    VeryHigh,
}

impl Default for NoiseSuppressionLevel {
    fn default() -> Self {
        Self::Moderate
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_processor_creation() {
        let processor = AudioProcessor::new();
        assert_eq!(processor.frame_size(), 480);
    }

    #[test]
    fn test_process_frame() {
        let mut processor = AudioProcessor::new();

        // 创建测试音频帧（480 samples @ 48kHz）
        let frame_size = processor.frame_size();
        let test_frame: Vec<f32> = (0..frame_size)
            .map(|i| (i as f32 / 20.0).sin() * 0.5)
            .collect();

        // 处理音频
        let result = processor.process(&test_frame);
        assert!(result.is_ok());

        let (processed, vad_prob) = result.unwrap();
        assert_eq!(processed.len(), frame_size);
        assert!(vad_prob >= 0.0 && vad_prob <= 1.0);
    }

    #[test]
    fn test_invalid_frame_size() {
        let mut processor = AudioProcessor::new();

        // 错误的帧大小
        let wrong_frame = vec![0.0f32; 100];
        let result = processor.process(&wrong_frame);
        assert!(result.is_err());

        if let Err(ProcessorError::InvalidFrameSize { expected, actual }) = result {
            assert_eq!(expected, 480);
            assert_eq!(actual, 100);
        } else {
            panic!("Expected InvalidFrameSize error");
        }
    }

    #[test]
    fn test_process_multiple_frames() {
        let mut processor = AudioProcessor::new();
        let frame_size = processor.frame_size();

        // 处理多个帧
        for _ in 0..10 {
            let test_frame: Vec<f32> = (0..frame_size).map(|i| (i as f32 / 20.0).sin()).collect();

            let result = processor.process(&test_frame);
            assert!(result.is_ok());
        }
    }

    #[test]
    fn test_noise_suppression_with_silence() {
        let mut processor = AudioProcessor::new();
        let frame_size = processor.frame_size();

        // 静音帧
        let silence_frame = vec![0.0f32; frame_size];

        let result = processor.process(&silence_frame);
        assert!(result.is_ok());

        let (processed, vad_prob) = result.unwrap();
        assert_eq!(processed.len(), frame_size);
        // 静音应该有低 VAD 概率
        assert!(vad_prob < 0.5);
    }
}
