# Project Alpha - Ticket 管理系统

基于标签的 Ticket 管理工具，提供简洁高效的任务跟踪和分类功能。

## 技术栈

- **后端**: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **前端**: React + TypeScript + Vite + Tailwind CSS + Shadcn UI
- **状态管理**: Zustand
- **数据获取**: Axios
- **通知**: Sonner

## 功能特性

- ✅ 创建、编辑、删除、完成 Ticket
- ✅ 批量操作（批量完成、批量删除）
- ✅ 基于标签的灵活分类
- ✅ 标签管理（创建、删除标签）
- ✅ 多维度过滤（状态、标签）
- ✅ 实时搜索（防抖优化）
- ✅ 排序功能（按创建时间、更新时间、标题）
- ✅ 响应式设计（移动端适配）
- ✅ 键盘快捷键支持
- ✅ 直观的用户界面

## 快速开始

### 前置要求

- Python 3.11+ (推荐使用 uv)
- Node.js 18+ (推荐使用 yarn)
- PostgreSQL 14+

### 后端设置

```bash
cd backend

# 使用 uv 安装依赖
uv sync

# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/projectalpha

# 创建数据库（如果不存在）
createdb projectalpha

# 运行数据库迁移
uv run alembic upgrade head

# （可选）导入种子数据
psql -U postgres -d projectalpha -f seed.sql

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

### 前端设置

```bash
cd frontend

# 安装依赖
yarn install

# 启动开发服务器
yarn dev
```

访问 <http://localhost:5173> 查看应用。

## 项目结构

```
project-alpha/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/     # API 路由
│   │   ├── crud/    # 数据库操作
│   │   ├── models/  # 数据模型
│   │   ├── schemas/ # Pydantic 模型
│   │   └── utils/   # 工具函数
│   ├── alembic/     # 数据库迁移
│   └── tests/       # 测试
├── frontend/        # React 前端
│   └── src/
│       ├── components/  # React 组件
│       ├── store/       # 状态管理
│       ├── types/       # TypeScript 类型
│       └── lib/         # 工具函数和 API 客户端
├── docs/           # 文档
│   └── test.rest   # REST Client 测试文件
└── specs/          # 项目规范文档
```

## API 文档

后端运行后访问:

- Swagger UI: <http://localhost:8000/api/v1/docs>
- ReDoc: <http://localhost:8000/api/v1/redoc>

## 开发

### 后端开发

```bash
# 运行测试
uv run pytest

# 代码格式化
uv run black app/
uv run isort app/

# 类型检查
uv run mypy app/
```

### 前端开发

```bash
# 构建
yarn build

# 预览构建
yarn preview

# 代码检查
yarn lint
```

## 键盘快捷键

- `Ctrl/Cmd + K`: 聚焦搜索框
- `N`: 创建新 Ticket（不在输入框时）
- `Esc`: 关闭对话框/侧边栏

## 测试

### 后端测试

```bash
cd backend
uv run pytest -v
```

### API 测试

使用 REST Client 测试文件：`docs/test.rest`

## 部署

### Docker 部署（推荐）

使用 Docker Compose 一键启动整个应用栈：

```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并清除数据
docker-compose down -v
```

服务架构：

```
localhost:3000 (frontend/nginx)
├── /api/* → backend:8000
└── /* → React SPA
            ↓
       postgres:5432
```

访问地址：
- 应用: http://localhost:3000
- API 文档: http://localhost:3000/api/v1/docs

### 本地开发部署

#### 生产环境变量

创建 `backend/.env.production`:

```env
DATABASE_URL=postgresql://user:password@host:5432/projectalpha
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
```

#### 启动应用

使用 Makefile 启动应用（从项目根目录运行）：

```bash
# 启动应用
make w1-start

# 停止应用
make w1-stop

# 安装依赖
make w1-install
```

## 许可证

MIT
