# DB Query Tool Constitution

<!--
Sync Impact Report:
Version: 1.0.0 (initial constitution for db_query project)
Created: 2025-11-16
Modified principles: N/A (initial version)
Added sections: All core principles established
Removed sections: None
Templates status:
  ✅ plan-template.md - aligned with constitution gates
  ✅ spec-template.md - aligned with requirement standards
  ✅ tasks-template.md - aligned with testing and quality principles
Follow-up TODOs: None
-->

## Core Principles

### I. Ergonomic Python with Strict Typing

**规则**: 所有后端代码必须使用 Ergonomic Python 风格编写，并包含严格的类型标注。

- Python 代码必须使用现代 Python 特性（Python 3.12+）
- 所有函数、方法、类属性必须包含类型注解
- 使用 `typing` 模块提供的类型工具（`Optional`, `Union`, `List`, `Dict` 等）
- 优先使用简洁、可读的代码风格
- 遵循 PEP 8 代码规范

**理由**: 严格的类型标注能够在开发阶段捕获类型错误，提高代码质量和可维护性。Ergonomic Python 风格使代码更易读、更易维护。

### II. Pydantic for Data Models

**规则**: 所有数据模型必须使用 Pydantic 定义。

- API 请求/响应模型使用 Pydantic BaseModel
- 数据库模型可以使用 SQLModel（基于 Pydantic）或 Pydantic + ORM
- 配置管理使用 Pydantic Settings
- 数据验证逻辑集中在 Pydantic 模型中
- 利用 Pydantic 的自动验证和序列化功能

**理由**: Pydantic 提供了类型安全的数据验证、序列化/反序列化功能，与 FastAPI 深度集成，减少样板代码并提高开发效率。

### III. camelCase JSON API Convention

**规则**: 所有后端生成的 JSON 数据必须使用 camelCase 命名格式。

- API 响应字段名使用 camelCase（如 `userId`, `createdAt`）
- Pydantic 模型配置 `alias_generator` 将 Python snake_case 自动转换为 camelCase
- 前端与后端的数据交换统一使用 camelCase
- 数据库列名可以使用 snake_case，但 API 层必须转换

**理由**: camelCase 是 JavaScript/TypeScript 的标准命名约定，保持 API 与前端代码风格一致，提供更好的开发体验。

### IV. TypeScript with Strict Type Safety

**规则**: 所有前端代码必须使用 TypeScript 编写，并启用严格类型检查。

- `tsconfig.json` 必须启用 `strict: true`
- 所有组件、函数、变量必须有明确的类型定义
- 禁止使用 `any` 类型（除非有充分理由并注释说明）
- API 响应数据必须定义对应的 TypeScript 接口
- 使用类型守卫和类型断言确保运行时类型安全

**理由**: 严格的类型检查能够在编译时发现潜在错误，提高代码质量，改善 IDE 支持，使重构更安全。

### V. No Authentication Required

**规则**: 应用程序不实现用户认证和授权机制。

- 任何用户都可以访问所有功能
- 不需要用户登录、注册或会话管理
- 数据库连接信息存储在应用本地（SQLite）
- 不实现用户隔离或数据权限控制

**理由**: 本项目是一个工具类应用，简化架构以专注于核心功能。在生产环境部署时应通过网络层（如 VPN、防火墙）控制访问。

### VI. SQL Safety and Query Validation

**规则**: 所有用户输入的 SQL 查询必须经过严格验证。

- 使用 `sqlglot` 或类似工具解析和验证 SQL 语法
- 仅允许执行 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP 等修改操作
- 自动为不包含 LIMIT 子句的查询添加 `LIMIT 1000`
- SQL 解析失败时返回清晰的错误信息
- 使用参数化查询防止 SQL 注入（当构建动态查询时）

**理由**: 确保数据库安全，防止用户意外或恶意修改数据库。限制结果集大小防止资源耗尽。

### VII. Test-Driven Development (Recommended)

**规则**: 关键功能应先编写测试，然后实现。

- API 端点应有集成测试验证请求/响应
- 数据模型应有单元测试验证序列化/反序列化
- SQL 解析和验证逻辑必须有测试覆盖
- 关键业务逻辑应有单元测试
- 使用 pytest 作为测试框架

**理由**: 测试驱动开发提高代码质量，确保功能正确性，使重构更安全。对于关键的安全功能（如 SQL 验证），测试尤为重要。

## Technology Stack

### Backend Requirements

- **Python**: ≥ 3.12，使用 uv 作为包管理器
- **Web Framework**: FastAPI（提供自动 API 文档、数据验证）
- **Data Validation**: Pydantic v2
- **SQL Parsing**: sqlglot（用于 SQL 语法验证和解析）
- **LLM Integration**: OpenAI SDK（用于自然语言生成 SQL）
- **Database**: SQLite（存储数据库连接和元数据）
- **ORM/Query Builder**: SQLAlchemy 或 SQLModel（可选，用于管理 SQLite）

### Frontend Requirements

- **Language**: TypeScript（严格模式）
- **Framework**: React 18+
- **Admin Framework**: Refine 5（提供 CRUD 脚手架）
- **UI Library**: Ant Design（与 Refine 深度集成）
- **Styling**: Tailwind CSS（实用优先的 CSS 框架）
- **Code Editor**: Monaco Editor（用于 SQL 编辑器）
- **Build Tool**: Vite（快速的开发和构建体验）

### Integration Requirements

- 后端提供 RESTful API，JSON 格式
- 前端通过 Refine 的 data provider 与后端集成
- API 响应使用 camelCase 字段名
- WebSocket 连接用于实时查询执行（可选）

## Development Workflow

### Code Quality Standards

- **Linting**:
  - Backend: ruff（Python linter 和 formatter）
  - Frontend: ESLint with TypeScript rules
- **Formatting**:
  - Backend: ruff format
  - Frontend: Prettier
- **Type Checking**:
  - Backend: mypy（Python 静态类型检查）
  - Frontend: tsc --noEmit
- **Pre-commit Hooks**: 配置 pre-commit 自动运行 linting 和 formatting

### Testing Standards

- **Backend**: pytest with coverage reporting (目标 >80%)
- **Frontend**: Vitest for unit tests, React Testing Library for component tests
- **Integration**: API 端点的端到端测试
- **CI/CD**: 自动运行所有测试和类型检查

### Documentation Requirements

- API endpoints documented via FastAPI automatic OpenAPI docs
- README.md with setup instructions and project overview
- Inline code comments for complex logic
- Type annotations serve as inline documentation

## Governance

### Amendment Process

- Constitution updates require justification and impact analysis
- Breaking changes to principles require major version bump
- New principles or significant expansions require minor version bump
- Clarifications and wording improvements require patch version bump

### Compliance Verification

- All PRs must align with constitution principles
- Code review checklist includes constitution compliance
- Complexity additions require explicit justification
- Regular audits to ensure ongoing compliance

### Version Control

- Constitution follows semantic versioning (MAJOR.MINOR.PATCH)
- Each amendment documents rationale and affected areas
- Constitution supersedes all other development practices

**Version**: 1.0.0 | **Ratified**: 2025-11-16 | **Last Amended**: 2025-11-16
