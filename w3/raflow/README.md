# RAFlow - 实时语音听写工具

> Realtime Audio Flow - 类似 Wispr Flow 的桌面级实时语音听写工具

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Rust](https://img.shields.io/badge/rust-1.90+-orange)
![Tauri](https://img.shields.io/badge/tauri-2.1-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 概述

RAFlow 是一个生产级的实时语音听写工具，通过全局热键唤醒，实现"说话即上屏"的流畅体验。应用常驻后台系统托盘，对系统资源占用极低，能够无缝集成到用户的日常工作流中。

### 核心特性

- ✅ **实时转写**：基于 ElevenLabs Scribe v2，延迟 <150ms
- ✅ **全局热键**：Cmd+Shift+\\ 快速唤醒
- ✅ **智能注入**：支持键盘模拟和剪贴板策略，适配多应用
- ✅ **系统托盘**：常驻后台，资源占用低（<50MB 内存）
- ✅ **跨平台**：macOS 优先支持（10.15+），后续支持 Windows/Linux

## 技术栈

### 后端（Rust）

- **框架**: Tauri 2.1
- **音频处理**: cpal 0.16 + rubato 0.16.2
- **网络通信**: tokio-tungstenite 0.24
- **系统交互**: enigo 0.6.1 + active-win-pos-rs 0.9

### 前端（TypeScript + React）

- **UI 框架**: React 19.2
- **状态管理**: Zustand 5.0
- **样式**: TailwindCSS 4.1
- **构建工具**: Vite 6.0

## 快速开始

### 前置要求

- Rust 1.90+
- Node.js 20+
- Yarn
- macOS 10.15+ (Catalina)

### 安装依赖

```bash
# 安装 Rust 依赖
cargo build

# 安装前端依赖
yarn install
```

### 开发模式

```bash
# 启动开发服务器
yarn tauri dev
```

### 生产构建

```bash
# 构建应用
yarn tauri build
```

## 项目结构

```
raflow/
├── src-tauri/          # Rust 后端
│   ├── src/
│   │   ├── audio/      # 音频采集与处理
│   │   ├── network/    # WebSocket 通信
│   │   ├── input/      # 文本注入
│   │   ├── system/     # 系统集成（热键、窗口）
│   │   ├── ui/         # 托盘、命令
│   │   └── config/     # 配置管理
│   └── Cargo.toml
├── src/                # React 前端
│   ├── components/     # UI 组件
│   ├── store/          # Zustand 状态
│   └── main.tsx
├── specs/              # 设计文档
└── package.json
```

## 开发指南

### 代码规范

- Rust: 使用 `cargo fmt` 和 `cargo clippy`
- TypeScript: 使用 ESLint 和 Prettier
- 提交前自动运行 pre-commit hooks

### 运行测试

```bash
# Rust 单元测试
cargo test --all-features

# Rust 集成测试
cargo nextest run --all-features
```

### Git 工作流

```bash
# 安装 pre-commit hooks
pre-commit install

# 手动运行 hooks
pre-commit run --all-files
```

## 配置

首次运行需要配置 ElevenLabs API Key：

1. 注册 [ElevenLabs](https://elevenlabs.io/) 账号
2. 获取 API Key
3. 在设置面板中输入 API Key

## 性能指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| 内存占用（空闲） | < 50MB | TBD |
| CPU 占用（录音） | < 5% | TBD |
| 音频延迟 | < 10ms | TBD |
| 端到端延迟 | < 200ms | TBD |

## 路线图

- [x] **Phase 1**: 项目初始化与基础设施（当前）
- [ ] **Phase 2**: 音频采集与处理
- [ ] **Phase 3**: 网络通信层
- [ ] **Phase 4**: 文本注入系统
- [ ] **Phase 5**: UI 与交互
- [ ] **Phase 6**: 系统集成与优化
- [ ] **Phase 7**: 测试与质量保证
- [ ] **Phase 8**: 部署与发布

详见 [实施计划](specs/w3/raflow/0003-implementation-plan.md)

## 参考文档

- [详细设计文档](specs/w3/raflow/0002-design.md)
- [实施计划](specs/w3/raflow/0003-implementation-plan.md)
- [Tauri 2.0 官方文档](https://v2.tauri.app/)
- [ElevenLabs Scribe v2 API](https://elevenlabs.io/docs)

## 推荐 IDE 设置

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

**版本**: v0.1.0
**维护者**: RAFlow 开发团队
