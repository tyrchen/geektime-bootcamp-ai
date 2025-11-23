//! 音频采集模块
//!
//! 基于 cpal 库实现跨平台音频采集

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Host, Stream, StreamConfig};
use thiserror::Error;
use tracing::{debug, info, warn};

#[derive(Error, Debug)]
pub enum CaptureError {
    #[error("No input device available")]
    NoDevice,

    #[error("Failed to get device config: {0}")]
    ConfigError(#[from] cpal::DefaultStreamConfigError),

    #[error("Failed to build audio stream: {0}")]
    StreamError(#[from] cpal::BuildStreamError),

    #[error("Failed to play audio stream: {0}")]
    PlayError(#[from] cpal::PlayStreamError),

    #[error("Device error: {0}")]
    DeviceError(String),
}

type Result<T> = std::result::Result<T, CaptureError>;

/// 音频采集器
pub struct AudioCapture {
    #[allow(dead_code)]
    host: Host,
    device: Device,
    config: StreamConfig,
    stream: Option<Stream>,
}

impl AudioCapture {
    /// 创建新的音频采集器，使用默认输入设备
    pub fn new() -> Result<Self> {
        let host = cpal::default_host();
        info!("Audio host: {:?}", host.id());

        let device = host.default_input_device().ok_or(CaptureError::NoDevice)?;

        let device_name = device.name().unwrap_or_else(|_| "Unknown".to_string());
        info!("Input device: {}", device_name);

        let config = device.default_input_config()?.into();
        debug!("Device config: {:?}", config);

        Ok(Self {
            host,
            device,
            config,
            stream: None,
        })
    }

    /// 使用指定设备创建音频采集器
    pub fn with_device(device_name: &str) -> Result<Self> {
        let host = cpal::default_host();

        let device = host
            .input_devices()
            .map_err(|e| CaptureError::DeviceError(e.to_string()))?
            .find(|d| d.name().map(|n| n.contains(device_name)).unwrap_or(false))
            .ok_or(CaptureError::NoDevice)?;

        let device_name_str = device.name().unwrap_or_else(|_| "Unknown".to_string());
        info!("Selected input device: {}", device_name_str);

        let config = device.default_input_config()?.into();
        debug!("Device config: {:?}", config);

        Ok(Self {
            host,
            device,
            config,
            stream: None,
        })
    }

    /// 启动音频流
    ///
    /// # Arguments
    /// * `callback` - 音频数据回调函数，每次接收到新的音频数据时调用（单声道数据）
    ///
    /// # Example
    /// ```no_run
    /// use raflow_lib::audio::AudioCapture;
    ///
    /// let mut capture = AudioCapture::new().unwrap();
    /// capture.start(|data| {
    ///     println!("Received {} samples", data.len());
    /// }).unwrap();
    /// ```
    pub fn start<F>(&mut self, mut callback: F) -> Result<()>
    where
        F: FnMut(&[f32]) + Send + 'static,
    {
        let error_callback = |err| {
            warn!("Audio stream error: {}", err);
        };

        let channels = self.config.channels;
        info!("Audio capture channels: {}", channels);

        let stream = self.device.build_input_stream(
            &self.config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                // 如果是立体声或多声道，转换为单声道
                if channels > 1 {
                    // 平均所有声道的数据转换为单声道
                    let mono_samples = data.len() / channels as usize;
                    let mut mono_data = Vec::with_capacity(mono_samples);

                    for i in 0..mono_samples {
                        let mut sum = 0.0f32;
                        for ch in 0..channels as usize {
                            sum += data[i * channels as usize + ch];
                        }
                        mono_data.push(sum / channels as f32);
                    }

                    callback(&mono_data);
                } else {
                    // 已经是单声道，直接传递
                    callback(data);
                }
            },
            error_callback,
            None,
        )?;

        stream.play()?;
        self.stream = Some(stream);
        info!("Audio stream started");

        Ok(())
    }

    /// 停止音频流
    pub fn stop(&mut self) {
        if let Some(stream) = self.stream.take() {
            drop(stream);
            info!("Audio stream stopped");
        }
    }

    /// 获取采样率
    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }

    /// 获取通道数
    pub fn channels(&self) -> u16 {
        self.config.channels
    }

    /// 列出所有可用的输入设备
    pub fn list_devices() -> Result<Vec<String>> {
        let host = cpal::default_host();
        let devices = host
            .input_devices()
            .map_err(|e| CaptureError::DeviceError(e.to_string()))?;

        let device_names: Vec<String> = devices.filter_map(|d| d.name().ok()).collect();

        Ok(device_names)
    }
}

impl Drop for AudioCapture {
    fn drop(&mut self) {
        self.stop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    };
    use std::time::Duration;

    #[test]
    fn test_audio_capture_initialization() {
        let capture = AudioCapture::new();
        assert!(capture.is_ok());
    }

    #[test]
    fn test_list_devices() {
        let devices = AudioCapture::list_devices();
        assert!(devices.is_ok());
        let device_list = devices.unwrap();
        println!("Available input devices: {:?}", device_list);
    }

    #[test]
    #[ignore] // 需要实际音频设备
    fn test_audio_stream_callback() {
        let mut capture = AudioCapture::new().unwrap();
        let counter = Arc::new(AtomicUsize::new(0));
        let counter_clone = counter.clone();

        capture
            .start(move |_data| {
                counter_clone.fetch_add(1, Ordering::Relaxed);
            })
            .unwrap();

        // 等待 100ms
        std::thread::sleep(Duration::from_millis(100));

        // 检查回调是否被调用
        let count = counter.load(Ordering::Relaxed);
        println!("Callback invoked {} times in 100ms", count);
        assert!(count > 0);
    }

    #[test]
    fn test_sample_rate() {
        let capture = AudioCapture::new().unwrap();
        let sample_rate = capture.sample_rate();
        println!("Sample rate: {} Hz", sample_rate);
        assert!(sample_rate > 0);
    }

    #[test]
    fn test_stereo_to_mono_conversion() {
        // 测试立体声到单声道的转换逻辑
        let channels = 2u16;
        let stereo_data = vec![
            1.0, 2.0, // 第一个样本: L=1.0, R=2.0
            3.0, 4.0, // 第二个样本: L=3.0, R=4.0
            5.0, 6.0, // 第三个样本: L=5.0, R=6.0
        ];

        // 模拟转换逻辑
        let mono_samples = stereo_data.len() / channels as usize;
        let mut mono_data = Vec::with_capacity(mono_samples);

        for i in 0..mono_samples {
            let mut sum = 0.0f32;
            for ch in 0..channels as usize {
                sum += stereo_data[i * channels as usize + ch];
            }
            mono_data.push(sum / channels as f32);
        }

        // 验证结果
        assert_eq!(mono_data.len(), 3);
        assert_eq!(mono_data[0], 1.5); // (1.0 + 2.0) / 2
        assert_eq!(mono_data[1], 3.5); // (3.0 + 4.0) / 2
        assert_eq!(mono_data[2], 5.5); // (5.0 + 6.0) / 2
    }
}
