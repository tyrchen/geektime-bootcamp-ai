# Instructions

## Basics

- 本项目在 ./w3/raflow 目录下，这是项目的根目录。
- 不要把任何用户要求以外的 *.md 放在项目根目录，请放在 ./docs 目录下。

## Rust

- 总是使用 Rust 2024，对于 dependencies 使用 workspace 管理，并访问 crate 相关的页面，了解其 API，确保使用最新的版本
- 优先使用 mpsc channel 而非 shared memory
- 对于很少改动的数据，如配置，优先考虑 ArcSwap 而非 Arc Mutex
- 如需并发 HashMap，优先考虑 DashMap 而非  Mutex/RwLock HashMap
- 不要使用任何 unsafe 代码，如果测试需要设置环境变量，使用 dotenv 库
- 不要使用 unwrap 或 expect 函数，而是正确处理或者 propagate error
- 使用 Rust 最新版本提供的 async trait 支持，而非 async_trait 库
