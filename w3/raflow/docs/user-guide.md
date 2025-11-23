# RAFlow 用户指南

> 实时语音转文字工具 - 简化版

## 快速开始

### 1. 首次配置

1. 启动应用后，点击系统托盘图标
2. 输入你的 ElevenLabs API Key
3. 点击保存

### 2. 使用流程

**超简单的 2 步操作：**

1. **按 Cmd+Shift+\\** → 开始录音（静默，无界面）
2. 说话...
3. **再按 Cmd+Shift+\\** → 停止录音
4. **转写文本自动写入剪贴板**
5. 在任何地方 **Cmd+V 粘贴**

就这么简单！

## 工作原理

```
按热键 → 开始录音 → 说话 → 再按热键 → 停止
   ↓
后台实时转写
   ↓
停止时：完整文本 → 剪贴板
   ↓
你手动粘贴（Cmd+V）到任何地方
```

## 技术细节

### 音频处理
- **采样率**: 48kHz → 16kHz 重采样
- **噪声抑制**: RNNoise 算法（自动）
- **质量**: Low 重采样（快速，够用）
- **延迟**: < 50ms
- **批量发送**: 每 500ms 发送一次到 API

#### 噪声抑制功能

RAFlow 集成了基于 RNNoise 的智能降噪技术：

- **自动启用**: 默认开启，支持 48kHz 采样率的设备
- **声道支持**: 自动将立体声/多声道转换为单声道处理
- **算法**: 循环神经网络 (RNN) 深度学习
- **效果**: 有效去除键盘、风扇、环境噪音
- **性能**: 低延迟（~10ms），低CPU占用（<5%）
- **采样率要求**: 设备必须支持 48kHz（如不支持则自动禁用降噪）
- **处理流程**:
  ```
  麦克风输入 (立体声 48kHz) → 转单声道 → 降噪处理 → 重采样 → 网络传输
  ```

> **重要提示**: RNNoise 严格要求 48kHz 采样率。如果你的设备不支持 48kHz，降噪功能会自动禁用，并在日志中显示 "Noise suppression disabled: device sample rate is XXXHz"。

### 网络通信
- **协议**: WebSocket (wss://)
- **API**: ElevenLabs Scribe v2
- **语言**: 中文（可在设置中修改）
- **批处理**: 500ms 音频块

### 剪贴板策略
- **停止时**: 完整转写 → 剪贴板
- **通知**: `transcript_ready` 事件
- **用户操作**: 手动 Cmd+V 粘贴

## 优势

### vs 复杂的 UI
- ✅ 无界面干扰
- ✅ 不影响工作流
- ✅ 完全后台运行

### vs 自动注入
- ✅ 用户完全控制
- ✅ 可以选择粘贴位置
- ✅ 避免误操作

### 性能优化
- ✅ 智能降噪（去除背景噪音）
- ✅ 批量发送（减少 API 调用）
- ✅ Low 质量重采样（更快）
- ✅ 200 块缓冲（~4秒）

## 故障排除

### 没有转写内容？

1. **检查 API Key**
   - 打开设置确认已配置
   - 查看日志是否有 "WebSocket connected"

2. **检查麦克风权限**
   - 系统偏好设置 → 隐私与安全 → 麦克风
   - 允许 RAFlow 访问

3. **检查剪贴板**
   - 停止录音后，在任意文本框按 Cmd+V
   - 应该看到转写文本

### Buffer Pool 警告？

如果看到 "Buffer pool exhausted"：
- 正常现象，不影响功能
- 已优化：容量 200，质量 Low
- 批量发送减少处理压力

### 转写不准确？

- 清晰地说话
- RNNoise 会自动去除大部分背景噪音，但仍建议在相对安静的环境录音
- 在设置中切换语言（如果需要）

### 噪声抑制相关

**降噪效果如何？**
- 有效去除：键盘声、风扇声、空调声、环境噪音
- 保留语音：人声质量基本不受影响
- 适用场景：办公室、家庭、咖啡厅等一般环境

**可以调整降噪强度吗？**
- 当前版本使用固定的 RNNoise 模型
- 默认配置已针对语音识别优化
- 未来版本将支持自定义降噪级别

## 日志示例

**成功的录音流程**:
```
INFO  Hotkey pressed - toggling recording
INFO  Starting recording (silent mode)
INFO  Audio stream started
INFO  Audio consumer task started
INFO  Noise suppression processor initialized  <-- 新增：降噪启用
INFO  Network manager started
INFO  WebSocket connected
INFO  Session started: session-xxx
DEBUG Sent batched audio: 8000 samples (~500ms)
INFO  Partial transcript: "你好"
INFO  Committed transcript: "你好，这是测试"
INFO  Transcript written to clipboard successfully
INFO  Hotkey pressed - toggling recording
INFO  Stopping recording
```

---

**享受无干扰的语音输入体验！** 🎤 → 📋 → ✍️
