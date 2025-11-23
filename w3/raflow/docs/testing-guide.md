# RAFlow 测试指南

> Phase 6 完成后的测试检查清单

## 已修复的问题

### ✅ 1. 热键闪退
- **问题**: `tokio::spawn` 在非 runtime 上下文
- **修复**: 使用 `std::thread::spawn`
- **状态**: 已修复

### ✅ 2. 热键行为
- **旧行为**: 按住开始，松开停止
- **新行为**: 按一次切换（toggle）
- **状态**: 已修复

### ✅ 3. 音频块大小不匹配
- **问题**: 重采样器期望 480，设备返回 1024
- **修复**: 动态适配块大小
- **状态**: 已修复

### ⚠️ 4. Buffer Pool 耗尽
- **问题**: 消费速度慢于生产速度
- **已优化**:
  - 缓冲区容量 100 → 200
  - 质量 High → Low（初始化更快）
  - 动态创建重采样器
- **状态**: 需要测试验证

### ❓ 5. 没有转写内容显示
- **可能原因**:
  1. API Key 未配置
  2. 网络连接未建立
  3. 前端未监听事件
- **状态**: 需要诊断

## 测试步骤

### 1. 配置 API Key

启动应用后：
1. 点击托盘图标
2. 在设置面板输入 ElevenLabs API Key
3. 点击保存

### 2. 测试热键

1. 按 **Cmd+Shift+\\**
2. **预期**: 悬浮窗出现
3. 开始说话
4. **预期**: 看到实时转写文本
5. 再按 **Cmd+Shift+\\**
6. **预期**: 悬浮窗消失

### 3. 检查日志

启动时应该看到：
```
✅ Audio consumer task started
✅ Resampler created in Xms
✅ Network manager started
✅ WebSocket connected
✅ Session started: session-xxx
```

### 4. 检查权限

macOS 会提示：
- ✅ 麦克风权限
- ✅ Accessibility 权限（用于文本注入）

## 当前已知问题

### 1. Buffer Pool 警告

**日志**:
```
WARN Buffer pool exhausted, allocating new Vec
```

**原因**: 消费者处理慢于生产
**影响**: 性能下降，但不影响功能
**优化**: 已增加容量和降低质量

### 2. 网络连接可能未启动

**症状**: 没有看到转写内容
**需要检查**:
1. AppController.start_recording() 是否被调用
2. NetworkManager.run() 是否启动
3. WebSocket 连接是否成功

### 3. 前端事件监听

**需要验证**:
- `transcript_update` 事件是否被监听
- 前端 console 是否有错误

## 调试命令

### 查看实时日志
```bash
RUST_LOG=debug cargo tauri dev
```

### 测试音频设备
```bash
cargo test --lib audio::capture::tests::test_list_devices -- --nocapture
```

### 测试文本注入
在设置界面的开发者工具中：
```javascript
await invoke('test_injection', { text: 'Hello, world!' });
```

## 下一步调试

### 如果没有转写内容：

1. **检查 API Key**
   ```javascript
   await invoke('get_config').then(console.log)
   ```

2. **检查网络连接**
   - 查看日志是否有 "WebSocket connected"
   - 查看日志是否有 "Session started"

3. **检查前端事件**
   - 打开悬浮窗的开发者工具
   - 查看 console 是否收到事件

4. **手动触发测试**
   ```javascript
   await invoke('start_recording');
   // 等待
   await invoke('stop_recording');
   ```

## 预期的完整日志流

```
INFO  Hotkey pressed - toggling recording
INFO  Current idle, starting recording
INFO  Start recording command
INFO  Control task: Start
INFO  Starting recording flow
INFO  Device sample rate: 48000Hz
INFO  Audio manager started
INFO  Audio stream started
INFO  Audio consumer task started
INFO  Creating resampler for chunk size: 1024
INFO  Resampler created in 2ms
INFO  Network manager started
INFO  WebSocket connected: status = 101
INFO  Session started: session-xxx
INFO  Partial transcript: "hello"
INFO  Committed transcript: "hello world" (confidence: 0.98)
INFO  Text injected successfully
```

---

**现在请测试应用，并报告:**
1. 是否还有 buffer pool 警告
2. 是否看到转写内容
3. 完整的日志输出
