# 贡献指南

感谢你考虑为 RAFlow 做出贡献！本文档概述了参与项目开发的流程。

## 开发环境设置

### 1. Fork 并克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/raflow.git
cd raflow
```

### 2. 安装依赖

```bash
# 安装 Rust 工具链
rustup toolchain install stable
rustup default stable

# 安装前端依赖
yarn install

# 安装 pre-commit hooks
pre-commit install
```

### 3. 创建开发分支

```bash
git checkout -b feature/your-feature-name
```

## 开发流程

### 代码规范

#### Rust 代码

- 遵循 [CLAUDE.md](CLAUDE.md) 中的 Rust 指导原则
- 使用 Rust 2024 edition
- 优先使用 workspace dependencies
- 避免使用 `unwrap()` 和 `expect()`，正确处理错误
- 不使用 `unsafe` 代码
- 优先使用 mpsc channel 而非 shared memory
- 使用 ArcSwap 而非 Arc<Mutex> 处理配置
- 使用 DashMap 而非 Mutex<HashMap> 实现并发 HashMap

#### TypeScript 代码

- 使用 ESLint 和 Prettier 格式化代码
- 遵循 React Hooks 最佳实践
- 避免使用 `any` 类型

### 提交前检查

```bash
# 格式化代码
cargo fmt --all
yarn format

# 运行 linter
cargo clippy --all-targets --all-features -- -D warnings
yarn lint

# 运行测试
cargo test --all-features
```

### 提交信息规范

使用语义化提交信息：

```
feat: 添加音频采集模块
fix: 修复 WebSocket 连接泄漏
docs: 更新 README
refactor: 重构文本注入逻辑
test: 添加重采样器单元测试
chore: 更新依赖版本
```

## Pull Request 流程

1. 确保所有测试通过
2. 更新相关文档
3. 提交 PR 到 `main` 分支
4. 在 PR 描述中说明：
   - 解决的问题
   - 实现方案
   - 测试方法
5. 等待代码审查

## 测试指南

### 单元测试

```bash
# Rust 单元测试
cargo test --lib

# 特定模块测试
cargo test --lib audio
```

### 集成测试

```bash
cargo nextest run --all-features
```

### 性能测试

```bash
cargo bench
```

## 项目结构

```
src-tauri/
├── src/
│   ├── audio/          # 音频采集与处理
│   ├── network/        # WebSocket 通信
│   ├── input/          # 文本注入
│   ├── system/         # 系统集成
│   ├── ui/             # UI 相关
│   ├── config/         # 配置管理
│   └── utils/          # 工具函数
```

## 常见问题

### Q: 如何运行特定的测试？

```bash
cargo test test_name
```

### Q: 如何调试 Rust 代码？

在 VS Code 中安装 CodeLLDB 扩展，然后使用调试配置。

### Q: 如何查看日志？

```bash
# 开发模式
RUST_LOG=debug cargo tauri dev
```

## 行为准则

- 尊重所有贡献者
- 提供建设性的反馈
- 专注于代码质量而非个人偏好

## 寻求帮助

- 提交 [Issue](https://github.com/raflow/raflow/issues)
- 加入讨论区

---

感谢你的贡献！
