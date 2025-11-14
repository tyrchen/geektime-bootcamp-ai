import { getUrl } from "../utils/url";

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
    previewImage: getUrl('/projects/project-1/preview.png'),
    demoUrl: 'http://localhost:5173',
  },
  {
    id: 'project-2',
    number: 2,
    title: '智能数据库查询生成器',
    subtitle: '自然语言转 SQL',
    difficulty: 3,
    estimatedHours: 6,
    weekNumber: 2,
    objectives: [
      '掌握复杂的 Prompt Engineering',
      '理解 AI 在数据处理中的应用',
      '学习错误处理和边缘情况',
      '实践 Cursor Composer 多文件编辑',
    ],
    techStack: ['React', 'TypeScript', 'Node.js', 'SQLite', 'Express'],
    architecture: `graph TB
    A[前端界面] --> B[自然语言输入]
    B --> C[AI 处理]
    C --> D[SQL 生成]
    D --> E[SQL 验证]
    E --> F{验证通过?}
    F -->|是| G[执行查询]
    F -->|否| H[错误提示]
    G --> I[结果展示]
    H --> B
    J[后端 API] --> K[SQLite]
    G --> J
    J --> I`,
    implementationSteps: [
      {
        stepNumber: 1,
        title: '搭建前后端架构',
        description: '使用 Composer 同时创建前端和后端代码',
      },
      {
        stepNumber: 2,
        title: '实现 NL2SQL 核心逻辑',
        description: '集成 AI API，将自然语言转换为 SQL',
        codeExample: `// 示例 Prompt 设计
const systemPrompt = \`你是一个 SQL 专家，将用户的自然语言查询转换为 SQL 语句。
数据库 schema: \${schema}
只返回 SQL 语句，不要有其他解释。\`;`,
      },
      {
        stepNumber: 3,
        title: '添加 SQL 验证和安全检查',
        description: '防止 SQL 注入，验证查询安全性',
      },
      {
        stepNumber: 4,
        title: '优化用户体验',
        description: '添加查询历史、结果导出等功能',
      },
    ],
    learningPoints: [
      'System Prompt 的设计技巧',
      '多文件协同编辑',
      'API 集成最佳实践',
      '错误处理和用户反馈',
    ],
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
