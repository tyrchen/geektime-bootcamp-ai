//! 音频重采样模块
//!
//! 使用 rubato 库实现高质量音频重采样，支持任意采样率转换

use rubato::{
    FastFixedIn, Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType,
    WindowFunction,
};
use thiserror::Error;
use tracing::debug;

#[derive(Error, Debug)]
pub enum ResamplerError {
    #[error("Resampler error: {0}")]
    RubatoError(String),

    #[error("Invalid input size: expected {expected}, got {actual}")]
    InvalidInputSize { expected: usize, actual: usize },

    #[error("Channel mismatch: expected {expected}, got {actual}")]
    ChannelMismatch { expected: usize, actual: usize },
}

type Result<T> = std::result::Result<T, ResamplerError>;

/// 重采样质量级别
#[derive(Debug, Clone, Copy)]
pub enum Quality {
    /// 低质量，快速处理
    Low,
    /// 中等质量
    Medium,
    /// 高质量，使用 Sinc 插值
    High,
}

/// 重采样器类型枚举
enum ResamplerType {
    Fast(FastFixedIn<f32>),
    Sinc(SincFixedIn<f32>),
}

/// 音频重采样器
pub struct AudioResampler {
    resampler: ResamplerType,
    input_buffer: Vec<Vec<f32>>,
    output_buffer: Vec<Vec<f32>>,
    chunk_size: usize,
    #[allow(dead_code)]
    channels: usize,
    input_rate: u32,
    output_rate: u32,
}

impl AudioResampler {
    /// 创建新的重采样器
    ///
    /// # Arguments
    /// * `input_rate` - 输入采样率（Hz）
    /// * `output_rate` - 输出采样率（Hz）
    /// * `chunk_size` - 输入块大小（采样点数量）
    /// * `channels` - 通道数
    /// * `quality` - 重采样质量
    ///
    /// # Example
    /// ```
    /// use raflow_lib::audio::{AudioResampler, Quality};
    ///
    /// // 48kHz -> 16kHz, 块大小 480 (10ms @ 48kHz), 单声道, 高质量
    /// let resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();
    /// ```
    pub fn new(
        input_rate: u32,
        output_rate: u32,
        chunk_size: usize,
        channels: usize,
        quality: Quality,
    ) -> Result<Self> {
        let ratio = output_rate as f64 / input_rate as f64;
        // 为 Sinc 重采样器预留额外空间（过渡带）
        let output_size = (chunk_size as f64 * ratio * 1.1).ceil() as usize;

        debug!(
            "Creating resampler: {}Hz -> {}Hz, chunk {} -> {}, {} channels, quality: {:?}",
            input_rate, output_rate, chunk_size, output_size, channels, quality
        );

        let resampler = match quality {
            Quality::Low | Quality::Medium => {
                // 使用快速插值
                let degree = match quality {
                    Quality::Low => rubato::PolynomialDegree::Linear,
                    _ => rubato::PolynomialDegree::Cubic,
                };

                ResamplerType::Fast(
                    FastFixedIn::<f32>::new(ratio, 2.0, degree, chunk_size, channels)
                        .map_err(|e| ResamplerError::RubatoError(e.to_string()))?,
                )
            }
            Quality::High => {
                // 使用 Sinc 插值，高质量设置
                let params = SincInterpolationParameters {
                    sinc_len: 256,
                    f_cutoff: 0.95,
                    interpolation: SincInterpolationType::Linear,
                    oversampling_factor: 256,
                    window: WindowFunction::BlackmanHarris2,
                };

                ResamplerType::Sinc(
                    SincFixedIn::<f32>::new(ratio, 2.0, params, chunk_size, channels)
                        .map_err(|e| ResamplerError::RubatoError(e.to_string()))?,
                )
            }
        };

        Ok(Self {
            resampler,
            input_buffer: vec![vec![0.0; chunk_size]; channels],
            output_buffer: vec![vec![0.0; output_size]; channels],
            chunk_size,
            channels,
            input_rate,
            output_rate,
        })
    }

    /// 处理音频数据并进行重采样
    ///
    /// # Arguments
    /// * `input` - 输入音频数据（交织格式，如立体声为 L, R, L, R, ...）
    ///
    /// # Returns
    /// * `Ok(Vec<f32>)` - 重采样后的音频数据（单声道格式）
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::audio::{AudioResampler, Quality};
    ///
    /// let mut resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();
    /// let input = vec![0.0; 480]; // 480 个采样点
    /// let output = resampler.process(&input).unwrap();
    /// assert_eq!(output.len(), 160); // 48k * 10ms -> 16k * 10ms
    /// ```
    pub fn process(&mut self, input: &[f32]) -> Result<Vec<f32>> {
        // 转为单声道（如果是立体声，取平均）
        let mono = if input.len() == self.chunk_size * 2 {
            // 立体声转单声道
            input
                .chunks_exact(2)
                .map(|chunk| (chunk[0] + chunk[1]) / 2.0)
                .collect::<Vec<_>>()
        } else if input.len() == self.chunk_size {
            // 已经是单声道
            input.to_vec()
        } else {
            return Err(ResamplerError::InvalidInputSize {
                expected: self.chunk_size,
                actual: input.len(),
            });
        };

        // 填充输入缓冲
        self.input_buffer[0].copy_from_slice(&mono);

        // 执行重采样（根据不同类型调用对应方法）
        let frames_out = match &mut self.resampler {
            ResamplerType::Fast(r) => {
                let (_, frames) = r
                    .process_into_buffer(&self.input_buffer, &mut self.output_buffer, None)
                    .map_err(|e| ResamplerError::RubatoError(e.to_string()))?;
                frames
            }
            ResamplerType::Sinc(r) => {
                let (_, frames) = r
                    .process_into_buffer(&self.input_buffer, &mut self.output_buffer, None)
                    .map_err(|e| ResamplerError::RubatoError(e.to_string()))?;
                frames
            }
        };

        // 返回重采样后的数据
        Ok(self.output_buffer[0][..frames_out].to_vec())
    }

    /// f32 -> i16 量化
    ///
    /// 将浮点音频数据（-1.0 到 1.0）转换为 16 位整数格式
    pub fn quantize_to_i16(samples: &[f32]) -> Vec<i16> {
        samples
            .iter()
            .map(|&sample| {
                let clamped = sample.clamp(-1.0, 1.0);
                (clamped * 32767.0) as i16
            })
            .collect()
    }

    /// 计算 RMS 音量（均方根）
    ///
    /// 用于音量检测和 UI 波形显示
    pub fn calculate_rms(samples: &[f32]) -> f32 {
        if samples.is_empty() {
            return 0.0;
        }

        let sum_squares: f32 = samples.iter().map(|&s| s * s).sum();
        (sum_squares / samples.len() as f32).sqrt()
    }

    /// 计算峰值音量
    pub fn calculate_peak(samples: &[f32]) -> f32 {
        samples
            .iter()
            .map(|&s| s.abs())
            .fold(0.0f32, |a, b| a.max(b))
    }

    /// 获取输入采样率
    pub fn input_rate(&self) -> u32 {
        self.input_rate
    }

    /// 获取输出采样率
    pub fn output_rate(&self) -> u32 {
        self.output_rate
    }

    /// 获取块大小
    pub fn chunk_size(&self) -> usize {
        self.chunk_size
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resampler_creation() {
        let resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High);
        assert!(resampler.is_ok());
    }

    #[test]
    fn test_resampling_48k_to_16k() {
        let mut resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();

        // 生成 480 个采样点的测试信号 (10ms @ 48kHz)
        let input: Vec<f32> = (0..480).map(|i| i as f32 / 480.0).collect();

        // SincFixedIn 初始阶段需要填充内部缓冲区，先运行几次
        for _ in 0..3 {
            let _ = resampler.process(&input);
        }

        // 现在应该达到稳态
        let output = resampler.process(&input).unwrap();

        println!("Output length: {}", output.len());
        // 稳态下，480 @ 48kHz 应该输出约 160 @ 16kHz
        assert!(output.len() >= 155 && output.len() <= 165);
    }

    #[test]
    fn test_stereo_to_mono() {
        let mut resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();

        // 立体声输入 (480 帧 * 2 通道 = 960 个采样点)
        let input: Vec<f32> = (0..960).map(|i| i as f32 / 960.0).collect();

        // 预热重采样器
        for _ in 0..3 {
            let _ = resampler.process(&input);
        }

        let output = resampler.process(&input).unwrap();

        println!("Output length: {}", output.len());
        assert!(output.len() >= 155 && output.len() <= 165);
    }

    #[test]
    fn test_quantize_to_i16() {
        let samples = vec![-1.0, -0.5, 0.0, 0.5, 1.0];
        let quantized = AudioResampler::quantize_to_i16(&samples);

        assert_eq!(quantized[0], -32767);
        assert_eq!(quantized[2], 0);
        assert_eq!(quantized[4], 32767);
    }

    #[test]
    fn test_calculate_rms() {
        // 静音信号
        let silence = vec![0.0; 100];
        assert_eq!(AudioResampler::calculate_rms(&silence), 0.0);

        // 单位幅度正弦波的 RMS 约为 0.707
        let sine: Vec<f32> = (0..1000)
            .map(|i| (2.0 * std::f32::consts::PI * i as f32 / 100.0).sin())
            .collect();
        let rms = AudioResampler::calculate_rms(&sine);
        assert!((rms - 0.707).abs() < 0.01);
    }

    #[test]
    fn test_calculate_peak() {
        let samples = vec![-0.8, 0.5, -0.3, 0.9, 0.1];
        let peak = AudioResampler::calculate_peak(&samples);
        assert_eq!(peak, 0.9);
    }

    #[test]
    fn test_different_qualities() {
        for quality in &[Quality::Low, Quality::Medium, Quality::High] {
            let mut resampler = AudioResampler::new(48000, 16000, 480, 1, *quality).unwrap();
            let input = vec![0.5; 480];

            // 预热重采样器
            for _ in 0..3 {
                let _ = resampler.process(&input);
            }

            let output = resampler.process(&input).unwrap();
            println!("Quality {:?}: output length = {}", quality, output.len());
            // 稳态输出应该接近 160
            assert!(output.len() >= 155 && output.len() <= 165);
        }
    }

    #[test]
    fn test_invalid_input_size() {
        let mut resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();
        let input = vec![0.0; 100]; // 错误的大小

        let result = resampler.process(&input);
        assert!(result.is_err());
    }
}
