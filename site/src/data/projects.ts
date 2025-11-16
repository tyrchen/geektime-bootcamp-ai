export interface ProjectData {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  difficulty: 1 | 2 | 3 | 4 | 5;
  estimatedHours: number;
  weekNumber: number;
  objectives: string[];
  techStack: string[];
  architecture: string;
  implementationSteps: {
    stepNumber: number;
    title: string;
    description: string;
    codeExample?: string;
  }[];
  learningPoints: string[];
  previewImage?: string;
  demoUrl?: string;
}

export const projects: ProjectData[] = [
  {
    id: 'project-1',
    number: 1,
    title: 'Ticket 管理系统',
    subtitle: '基于标签的任务追踪工具',
    difficulty: 2,
    estimatedHours: 8,
    weekNumber: 1,
    objectives: [
      '快速掌握 AI 工具的核心功能',
      '将 AI 工具应用于实用的原型构建',
      '体验 AI 辅助编码的效率',
      '理解前后端分离的全栈架构',
    ],
    techStack: [
      'React',
      'TypeScript',
      'Vite',
      'Tailwind CSS',
      'Shadcn UI',
      'Zustand',
      'FastAPI',
      'PostgreSQL',
      'SQLAlchemy',
      'Alembic',
    ],
    architecture: `graph TB
    subgraph "前端层"
      A[React + TypeScript]
      B[Shadcn UI 组件]
      C[Zustand 状态管理]
    end

    subgraph "网络层"
      D[Axios HTTP Client]
    end

    subgraph "后端层"
      E[FastAPI]
      F[Pydantic 验证]
    end

    subgraph "数据层"
      G[SQLAlchemy ORM]
      H[PostgreSQL]
    end

    subgraph "数据库表"
      I[tickets 表]
      J[tags 表]
      K[ticket_tags 关联表]
    end

    A --> B
    A --> C
    A --> D
    D --> E
    E --> F
    E --> G
    G --> H
    H --> I
    H --> J
    H --> K
    I -.多对多.-> K
    J -.多对多.-> K`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '数据库设计和迁移',
        description:
          '设计 tickets、tags、ticket_tags 三张表，使用 Alembic 创建迁移脚本',
        codeExample: `-- tickets 表
CREATE TABLE tickets (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- tags 表
CREATE TABLE tags (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ticket_tags 关联表
CREATE TABLE ticket_tags (
    ticket_id BIGINT REFERENCES tickets(id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (ticket_id, tag_id)
);`,
      },
      {
        stepNumber: 2,
        title: '后端 API 开发',
        description:
          '使用 FastAPI 实现 RESTful API，包含 CRUD 操作、搜索、过滤等功能',
        codeExample: `@router.get("", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = Query(None),
    tag_ids: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db)
) -> TicketListResponse:
    """获取 Ticket 列表，支持过滤、搜索和排序"""
    tickets = crud.get_tickets(
        db, status=status, tag_ids=tag_ids,
        search=search, sort_by=sort_by, order=order
    )
    return TicketListResponse(tickets=tickets, total=len(tickets))`,
      },
      {
        stepNumber: 3,
        title: '前端状态管理',
        description:
          '使用 Zustand 管理全局状态，包含 tickets、tags、过滤条件等',
        codeExample: `interface TicketStore {
  tickets: Ticket[];
  tags: Tag[];
  statusFilter: 'all' | 'pending' | 'completed';
  selectedTagIds: number[];
  searchQuery: string;
  sortBy: 'created_at' | 'updated_at' | 'title';
  sortOrder: 'asc' | 'desc';

  // Actions
  fetchTickets: () => Promise<void>;
  createTicket: (data: CreateTicketData) => Promise<void>;
  updateTicket: (id: number, data: UpdateTicketData) => Promise<void>;
  deleteTicket: (id: number) => Promise<void>;
  toggleTicketStatus: (id: number) => Promise<void>;
  setStatusFilter: (status: 'all' | 'pending' | 'completed') => void;
  toggleTagFilter: (tagId: number) => void;
  setSearchQuery: (query: string) => void;
}`,
      },
      {
        stepNumber: 4,
        title: 'UI 组件开发',
        description:
          '使用 Shadcn UI 构建响应式界面，包含 Ticket 卡片、对话框、侧边栏等',
        codeExample: `import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

// 创建 Ticket 对话框组件
function CreateTicketDialog({ open, onOpenChange }) {
  const createTicket = useTicketStore((state) => state.createTicket);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await createTicket({ title, description, tagIds });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>创建 Ticket</DialogHeader>
        <form onSubmit={handleSubmit}>
          <Input placeholder="输入 Ticket 标题" />
          <Textarea placeholder="输入描述（可选）" />
          <Button type="submit">创建</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}`,
      },
      {
        stepNumber: 5,
        title: '高级功能实现',
        description:
          '实现搜索防抖、批量操作、键盘快捷键等高级特性',
        codeExample: `// 搜索防抖
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    setSearchQuery(query);
  }, 300),
  []
);

// 批量操作
const handleBatchComplete = () => {
  const selectedIds = tickets
    .filter((t) => selectedTicketIds.includes(t.id))
    .map((t) => t.id);

  Promise.all(selectedIds.map((id) => toggleTicketStatus(id)));
};

// 键盘快捷键 (Ctrl+K 打开搜索)
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      searchInputRef.current?.focus();
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);`,
      },
    ],
    learningPoints: [
      '如何设计清晰的 RESTful API',
      'FastAPI 的自动文档生成和类型验证',
      'PostgreSQL 的多对多关系设计',
      'Shadcn UI 组件的定制和使用',
      'Zustand 轻量级状态管理',
      '响应式布局的最佳实践',
      '前后端协作的开发流程',
      '使用 Alembic 管理数据库版本',
    ],
    previewImage: 'projects/project-1/preview.png',
    demoUrl: 'http://localhost:5173',
  },
  {
    id: 'project-2',
    number: 2,
    title: '数据库查询工具',
    subtitle: '支持自然语言生成 SQL 的智能数据库管理平台',
    difficulty: 3,
    estimatedHours: 12,
    weekNumber: 2,
    objectives: [
      '掌握复杂的 Prompt Engineering 技巧',
      '理解 AI 在数据处理中的实际应用',
      '学习 SQL 安全验证和错误处理',
      '实践全栈应用的架构设计',
      '使用现代化前端框架（React 19 + Refine 5）',
      '掌握严格的类型安全（Python + TypeScript）',
    ],
    techStack: [
      'React 19',
      'TypeScript',
      'Refine 5',
      'Ant Design 5',
      'Monaco Editor',
      'Tailwind CSS 4',
      'Vite',
      'FastAPI',
      'Python 3.12+',
      'Pydantic v2',
      'SQLite',
      'PostgreSQL',
      'sqlglot',
      'OpenAI SDK',
      'asyncpg',
    ],
    architecture: `graph TB
    subgraph "前端层"
      A[React 19 + TypeScript]
      B[Refine 5 框架]
      C[Ant Design 5 UI]
      D[Monaco SQL 编辑器]
    end

    subgraph "网络层"
      E[Axios HTTP Client]
      F[Refine Data Provider]
    end

    subgraph "后端 API 层"
      G[FastAPI]
      H[Pydantic v2 验证]
      I[API Routes]
    end

    subgraph "业务逻辑层"
      J[SQL 验证服务 - sqlglot]
      K[元数据提取服务]
      L[查询执行服务]
      M[自然语言转 SQL - OpenAI]
    end

    subgraph "数据层"
      N[本地 SQLite]
      O[远程 PostgreSQL]
    end

    subgraph "存储实体"
      P[DatabaseConnection]
      Q[DatabaseMetadata]
      R[QueryHistory]
    end

    A --> B
    B --> C
    B --> D
    B --> F
    F --> E
    E --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    I --> M
    J --> L
    K --> O
    L --> O
    M --> O
    G --> N
    N --> P
    N --> Q
    N --> R`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '数据模型和 API 规范设计',
        description:
          '使用 Pydantic 定义严格的数据模型，设计 RESTful API 接口，确保类型安全和 camelCase JSON 规范',
        codeExample: `from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class DatabaseConnectionCreate(BaseModel):
    """创建数据库连接的请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100)
    connection_url: str = Field(..., min_length=1)
    description: Optional[str] = None

class DatabaseMetadataResponse(BaseModel):
    """数据库元数据响应模型"""
    model_config = ConfigDict(alias_generator=to_camel)

    database_name: str
    tables: list[TableMetadata]
    fetched_at: datetime

class TableMetadata(BaseModel):
    table_name: str
    table_type: str  # 'TABLE' or 'VIEW'
    columns: list[ColumnMetadata]`,
      },
      {
        stepNumber: 2,
        title: 'SQL 安全验证服务',
        description:
          '使用 sqlglot 解析和验证 SQL 语句，仅允许 SELECT 查询，自动添加 LIMIT 1000 限制',
        codeExample: `import sqlglot
from sqlglot import exp, parse_one

class SQLValidator:
    def validate_and_transform(self, sql: str) -> tuple[str, Optional[str]]:
        """验证 SQL 并自动添加 LIMIT"""
        try:
            # 解析 SQL
            parsed = parse_one(sql, dialect="postgres")

            # 检查是否为 SELECT 语句
            if not isinstance(parsed, exp.Select):
                return None, "仅允许 SELECT 查询"

            # 检查是否包含非法操作（子查询中的 INSERT/UPDATE/DELETE）
            for node in parsed.walk():
                if isinstance(node, (exp.Insert, exp.Update, exp.Delete)):
                    return None, "不允许执行修改操作"

            # 自动添加 LIMIT 1000
            if not parsed.args.get("limit"):
                parsed = parsed.limit(1000)

            return parsed.sql(dialect="postgres"), None

        except Exception as e:
            return None, f"SQL 语法错误: {str(e)}"`,
      },
      {
        stepNumber: 3,
        title: '数据库元数据提取',
        description:
          '连接 PostgreSQL 数据库，提取完整的表结构、列定义、数据类型等元数据信息',
        codeExample: `import asyncpg
from typing import List

class MetadataService:
    async def fetch_metadata(self, connection_url: str) -> DatabaseMetadata:
        """获取数据库完整元数据"""
        conn = await asyncpg.connect(connection_url)

        try:
            # 获取所有表和视图
            tables = await conn.fetch("""
                SELECT
                    table_name,
                    table_type,
                    table_schema
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_name
            """)

            metadata = []
            for table in tables:
                # 获取列信息
                columns = await conn.fetch("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = $2
                    ORDER BY ordinal_position
                """, table['table_name'], table['table_schema'])

                metadata.append(TableMetadata(
                    table_name=table['table_name'],
                    table_type=table['table_type'],
                    columns=[ColumnMetadata(**dict(col)) for col in columns]
                ))

            return DatabaseMetadata(
                database_name=conn.get_server_pid(),
                tables=metadata,
                fetched_at=datetime.utcnow()
            )
        finally:
            await conn.close()`,
      },
      {
        stepNumber: 4,
        title: '自然语言转 SQL（NL2SQL）',
        description:
          '集成 OpenAI API，结合数据库元数据上下文，将自然语言查询需求转换为 SQL 语句',
        codeExample: `from openai import AsyncOpenAI

class NL2SQLService:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def generate_sql(
        self,
        natural_language: str,
        metadata: DatabaseMetadata
    ) -> str:
        """将自然语言转换为 SQL"""

        # 构建数据库 schema 上下文
        schema_context = self._build_schema_context(metadata)

        system_prompt = f"""你是一个 PostgreSQL SQL 专家。
根据用户的自然语言描述，生成准确的 SQL SELECT 查询。

数据库结构：
{schema_context}

要求：
1. 只生成 SELECT 语句
2. 使用正确的表名和列名
3. 考虑数据类型和约束
4. 返回纯 SQL，不要有任何解释
5. 使用标准 PostgreSQL 语法"""

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_language}
            ],
            temperature=0.1,
        )

        sql = response.choices[0].message.content.strip()
        # 移除可能的 markdown 代码块标记
        sql = sql.replace('\`\`\`sql', '').replace('\`\`\`', '').strip()

        return sql

    def _build_schema_context(self, metadata: DatabaseMetadata) -> str:
        """构建 schema 描述供 LLM 理解"""
        context = []
        for table in metadata.tables:
            cols = ", ".join([
                f"{c.column_name} {c.data_type}"
                for c in table.columns
            ])
            context.append(f"{table.table_name} ({cols})")
        return "\\n".join(context)`,
      },
      {
        stepNumber: 5,
        title: 'FastAPI 路由和端点实现',
        description:
          '实现完整的 RESTful API，包括数据库连接管理、元数据获取、查询执行等功能',
        codeExample: `from fastapi import APIRouter, Depends, HTTPException
from app.services.sql_validator import SQLValidator
from app.services.metadata import MetadataService
from app.services.query import QueryService
from app.services.nl2sql import NL2SQLService

router = APIRouter(prefix="/api/v1/dbs", tags=["databases"])

@router.post("", response_model=DatabaseResponse)
async def create_database_connection(
    data: DatabaseConnectionCreate,
    db: Session = Depends(get_db)
):
    """添加数据库连接"""
    # 验证连接是否有效
    metadata_service = MetadataService()
    try:
        await metadata_service.test_connection(data.connection_url)
    except Exception as e:
        raise HTTPException(400, f"数据库连接失败: {str(e)}")

    # 保存到 SQLite
    db_conn = DatabaseConnection(**data.model_dump())
    db.add(db_conn)
    db.commit()
    db.refresh(db_conn)

    return db_conn

@router.post("/{db_name}/query/execute", response_model=QueryResultResponse)
async def execute_query(
    db_name: str,
    request: QueryExecuteRequest,
    db: Session = Depends(get_db)
):
    """执行 SQL 查询"""
    # 获取数据库连接
    db_conn = db.query(DatabaseConnection).filter_by(name=db_name).first()
    if not db_conn:
        raise HTTPException(404, "数据库连接不存在")

    # SQL 验证
    validator = SQLValidator()
    validated_sql, error = validator.validate_and_transform(request.sql)
    if error:
        raise HTTPException(400, error)

    # 执行查询
    query_service = QueryService()
    try:
        result = await query_service.execute(
            db_conn.connection_url,
            validated_sql
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"查询执行失败: {str(e)}")

@router.post("/{db_name}/query/nl2sql", response_model=NL2SQLResponse)
async def natural_language_to_sql(
    db_name: str,
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """将自然语言转换为 SQL"""
    # 获取数据库元数据
    metadata = await get_cached_metadata(db_name, db)

    # 调用 NL2SQL 服务
    nl2sql_service = NL2SQLService()
    sql = await nl2sql_service.generate_sql(
        request.natural_language,
        metadata
    )

    return NL2SQLResponse(generated_sql=sql)`,
      },
      {
        stepNumber: 6,
        title: '前端页面和组件开发',
        description:
          '使用 React 19 + Refine 5 构建现代化界面，包含数据库列表、元数据浏览、SQL 编辑器和结果展示',
        codeExample: `import { Refine } from "@refinedev/core";
import { dataProvider } from "@refinedev/simple-rest";
import { DatabaseList } from "./pages/databases/list";
import { QueryExecute } from "./pages/queries/execute";

function App() {
  return (
    <Refine
      dataProvider={dataProvider("http://localhost:8000/api/v1")}
      resources={[
        {
          name: "dbs",
          list: "/databases",
          create: "/databases/create",
          show: "/databases/:name",
        },
      ]}
      routes={[
        {
          path: "/databases/:name/query",
          element: <QueryExecute />,
        },
      ]}
    >
      <Routes>
        <Route path="/databases" element={<DatabaseList />} />
        <Route path="/databases/:name/query" element={<QueryExecute />} />
      </Routes>
    </Refine>
  );
}

// Monaco SQL 编辑器组件
import Editor from "@monaco-editor/react";

export function SqlEditor({ value, onChange, onExecute }) {
  return (
    <div className="sql-editor">
      <Editor
        height="300px"
        language="sql"
        theme="vs-dark"
        value={value}
        onChange={onChange}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: "on",
          automaticLayout: true,
        }}
      />
      <Button onClick={onExecute} type="primary">
        执行查询 (Ctrl+Enter)
      </Button>
    </div>
  );
}`,
      },
      {
        stepNumber: 7,
        title: '查询结果展示和导出',
        description:
          '实现表格化结果展示，支持分页、排序，提供 CSV 和 JSON 导出功能',
        codeExample: `import { Table, Button } from "antd";
import { DownloadOutlined } from "@ant-design/icons";

export function ResultTable({ result }) {
  const columns = result.columns.map(col => ({
    title: col.name,
    dataIndex: col.name,
    key: col.name,
    sorter: true,
  }));

  const handleExportCSV = () => {
    const csv = [
      result.columns.map(c => c.name).join(","),
      ...result.rows.map(row =>
        result.columns.map(c => row[c.name]).join(",")
      )
    ].join("\\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = \`query_result_\${Date.now()}.csv\`;
    a.click();
  };

  return (
    <div>
      <div className="result-header">
        <span>返回 {result.row_count} 行 · 执行时间: {result.execution_time}ms</span>
        <Button icon={<DownloadOutlined />} onClick={handleExportCSV}>
          导出 CSV
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={result.rows}
        pagination={{ pageSize: 50 }}
        scroll={{ x: true, y: 600 }}
      />
    </div>
  );
}`,
      },
      {
        stepNumber: 8,
        title: '测试和优化',
        description:
          '编写单元测试和集成测试，优化 SQL 验证逻辑，改进用户体验',
        codeExample: `import pytest
from app.services.sql_validator import SQLValidator

class TestSQLValidator:
    def setup_method(self):
        self.validator = SQLValidator()

    def test_valid_select(self):
        sql = "SELECT * FROM users"
        result, error = self.validator.validate_and_transform(sql)
        assert error is None
        assert "LIMIT 1000" in result

    def test_reject_insert(self):
        sql = "INSERT INTO users (name) VALUES ('test')"
        result, error = self.validator.validate_and_transform(sql)
        assert result is None
        assert "仅允许 SELECT" in error

    def test_reject_delete(self):
        sql = "DELETE FROM users WHERE id = 1"
        result, error = self.validator.validate_and_transform(sql)
        assert result is None
        assert "仅允许 SELECT" in error

    def test_auto_add_limit(self):
        sql = "SELECT id, name FROM users"
        result, error = self.validator.validate_and_transform(sql)
        assert "LIMIT 1000" in result

    def test_preserve_existing_limit(self):
        sql = "SELECT * FROM users LIMIT 10"
        result, error = self.validator.validate_and_transform(sql)
        assert "LIMIT 10" in result
        assert "LIMIT 1000" not in result`,
      },
    ],
    learningPoints: [
      '使用 Pydantic v2 实现严格的数据验证和类型安全',
      '掌握 FastAPI 的异步编程和依赖注入',
      '使用 sqlglot 进行 SQL 解析和安全验证',
      '设计有效的 Prompt 工程（System Prompt + Schema Context）',
      'OpenAI API 集成和错误处理最佳实践',
      'React 19 + Refine 5 现代化前端架构',
      'Monaco Editor 集成和 SQL 语法高亮',
      '异步数据库操作（asyncpg）',
      'API 接口的 RESTful 设计规范',
      'camelCase JSON 命名规范在 Python/TypeScript 中的实现',
      '全栈应用的错误处理和用户反馈',
      'pytest 单元测试和集成测试编写',
    ],
    previewImage: 'projects/project-2/preview.jpg',
    demoUrl: 'http://localhost:5173',
  },
  {
    id: 'project-3',
    number: 3,
    title: 'MCP Server 开发：知识库助手',
    subtitle: '打造个人 AI 知识库',
    difficulty: 4,
    estimatedHours: 8,
    weekNumber: 5,
    objectives: [
      '深入理解 MCP 协议',
      '开发自定义 MCP Server',
      '实现 Resources、Tools、Prompts',
      '集成到 Claude Desktop',
    ],
    techStack: ['Python', 'FastMCP', 'Vector Database', 'Markdown'],
    architecture: `graph TB
    A[Claude Desktop] <--> B[MCP Client]
    B <--> C[MCP Server]
    C --> D[Resources]
    C --> E[Tools]
    C --> F[Prompts]
    D --> G[知识库文档]
    D --> H[向量数据库]
    E --> I[搜索工具]
    E --> J[总结工具]
    F --> K[查询模板]
    F --> L[总结模板]`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '初始化 MCP Server 项目',
        description: '使用 FastMCP 框架搭建基础结构',
        codeExample: `# 使用 Claude Code 生成 MCP Server 模板
# Prompt: 创建一个 FastMCP server，实现知识库管理功能`,
      },
      {
        stepNumber: 2,
        title: '实现 Resources',
        description: '提供文档资源的访问接口',
      },
      {
        stepNumber: 3,
        title: '开发 Tools',
        description: '实现搜索、总结、问答等工具',
      },
      {
        stepNumber: 4,
        title: '配置 Prompts',
        description: '预定义常用的查询提示词',
      },
      {
        stepNumber: 5,
        title: '集成到 Claude Desktop',
        description: '配置 MCP server 并测试功能',
      },
    ],
    learningPoints: [
      'MCP 协议的深入理解',
      'Python 异步编程',
      '向量数据库的使用',
      'AI 工具链整合',
    ],
  },
  {
    id: 'project-4',
    number: 4,
    title: 'Code Review Agent',
    subtitle: '自动化代码审查助手',
    difficulty: 4,
    estimatedHours: 10,
    weekNumber: 6,
    objectives: [
      '理解 Agent 的设计和实现',
      '掌握 Function Calling',
      '学习代码质量分析',
      '实践 ReAct 模式',
    ],
    techStack: ['Python', 'LangChain', 'Claude API', 'GitHub API', 'AST Parser'],
    architecture: `graph TB
    A[代码输入] --> B[Agent 规划]
    B --> C[代码分析]
    C --> D[静态分析]
    C --> E[安全检查]
    C --> F[最佳实践]
    D --> G[问题收集]
    E --> G
    F --> G
    G --> H[AI 评审]
    H --> I[生成报告]
    I --> J[改进建议]`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '设计 Agent 架构',
        description: '实现 ReAct 模式的 Agent',
        codeExample: `# Agent 思考 -> 行动 -> 观察 -> 思考 循环
class CodeReviewAgent:
    def think(self, observation):
        # AI 分析当前情况，规划下一步
        pass

    def act(self, plan):
        # 调用工具执行计划
        pass

    def observe(self, result):
        # 收集执行结果
        pass`,
      },
      {
        stepNumber: 2,
        title: '实现分析工具',
        description: '开发代码分析、安全检查等工具',
      },
      {
        stepNumber: 3,
        title: '集成 Function Calling',
        description: '让 AI 自主选择和调用工具',
      },
      {
        stepNumber: 4,
        title: '生成审查报告',
        description: '结构化输出审查结果和建议',
      },
      {
        stepNumber: 5,
        title: '优化和测试',
        description: '在真实项目上测试和优化 Agent',
      },
    ],
    learningPoints: [
      'Agent 设计模式（ReAct）',
      'Function Calling 实战',
      '代码静态分析',
      'Prompt 工程高级技巧',
    ],
  },
  {
    id: 'project-5',
    number: 5,
    title: '全栈 AI 应用：智能文档助手',
    subtitle: '端到端开发实践',
    difficulty: 5,
    estimatedHours: 16,
    weekNumber: 7,
    objectives: [
      '整合所有学到的工具和技能',
      '实践完整的开发流程',
      '构建生产级应用',
      '学习部署和运维',
    ],
    techStack: [
      'React',
      'TypeScript',
      'Node.js',
      'PostgreSQL',
      'Vector DB',
      'Docker',
      'MCP',
      'Claude API',
    ],
    architecture: `graph TB
    A[Web 前端] --> B[API Gateway]
    B --> C[认证服务]
    B --> D[文档服务]
    B --> E[AI 服务]
    D --> F[PostgreSQL]
    D --> G[Vector DB]
    E --> H[Claude API]
    E --> I[MCP Server]
    I --> J[外部工具]
    I --> K[数据源]`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '需求分析和架构设计',
        description: '使用 Claude Code 生成技术方案',
      },
      {
        stepNumber: 2,
        title: '前端开发',
        description: '使用 Cursor 快速构建 React 应用',
      },
      {
        stepNumber: 3,
        title: '后端 API 开发',
        description: 'Node.js + Express 实现 RESTful API',
      },
      {
        stepNumber: 4,
        title: '数据库设计和实现',
        description: 'PostgreSQL + Vector DB 混合存储',
      },
      {
        stepNumber: 5,
        title: 'AI 功能集成',
        description: '接入 Claude API 和 MCP Server',
      },
      {
        stepNumber: 6,
        title: '测试和优化',
        description: 'AI 辅助的单元测试和集成测试',
      },
      {
        stepNumber: 7,
        title: 'Docker 化和部署',
        description: '容器化应用并部署到云平台',
      },
    ],
    learningPoints: [
      '全栈开发流程',
      '多工具协同使用',
      'AI 驱动的开发模式',
      '生产级应用最佳实践',
      'DevOps 和 CI/CD',
    ],
  },
];

// 根据 ID 获取项目
export const getProjectById = (id: string): ProjectData | undefined => {
  return projects.find((project) => project.id === id);
};

// 根据周数获取项目
export const getProjectsByWeek = (weekNumber: number): ProjectData[] => {
  return projects.filter((project) => project.weekNumber === weekNumber);
};

// 根据难度获取项目
export const getProjectsByDifficulty = (
  difficulty: ProjectData['difficulty']
): ProjectData[] => {
  return projects.filter((project) => project.difficulty === difficulty);
};
