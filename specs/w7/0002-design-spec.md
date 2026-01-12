# GenSlides 设计规格文档

## 1. 项目目录结构

```
genslides/
├── backend/                          # 后端代码
│   ├── main.py                       # FastAPI 应用入口
│   ├── config.py                     # 配置管理
│   ├── api/                          # API 层 - 处理 HTTP 请求/响应
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── slides.py             # Slides 相关路由
│   │   │   ├── images.py             # 图片相关路由
│   │   │   ├── style.py              # 风格相关路由
│   │   │   └── cost.py               # 成本统计路由
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── slide.py
│   │   │   ├── image.py
│   │   │   ├── style.py
│   │   │   └── cost.py
│   │   └── dependencies.py           # 依赖注入
│   ├── services/                     # 业务层 - 业务逻辑处理
│   │   ├── __init__.py
│   │   ├── slide_service.py          # Slide 业务逻辑
│   │   ├── image_service.py          # 图片生成业务逻辑
│   │   ├── style_service.py          # 风格管理业务逻辑
│   │   └── cost_service.py           # 成本计算业务逻辑
│   ├── repositories/                 # 存储层 - 数据持久化
│   │   ├── __init__.py
│   │   ├── slide_repository.py       # Slide 数据存储
│   │   └── image_repository.py       # 图片文件存储
│   ├── models/                       # 领域模型
│   │   ├── __init__.py
│   │   ├── slide.py
│   │   ├── project.py
│   │   └── style.py
│   ├── clients/                      # 外部服务客户端
│   │   ├── __init__.py
│   │   └── gemini_client.py          # Google AI SDK 封装
│   └── utils/                        # 工具函数
│       ├── __init__.py
│       └── hash.py                   # Blake3 哈希计算
│
├── frontend/                         # 前端代码
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx                  # 应用入口
│       ├── App.tsx                   # 根组件
│       ├── api/                      # API 请求封装
│       │   ├── index.ts
│       │   ├── slides.ts
│       │   ├── images.ts
│       │   └── style.ts
│       ├── stores/                   # Zustand 状态管理
│       │   ├── index.ts
│       │   ├── slideStore.ts
│       │   └── playerStore.ts
│       ├── components/               # UI 组件
│       │   ├── layout/
│       │   │   ├── Header.tsx        # 顶部导航栏
│       │   │   ├── Sidebar.tsx       # 左侧边栏
│       │   │   └── MainContent.tsx   # 主内容区
│       │   ├── slides/
│       │   │   ├── SlideList.tsx     # Slide 列表
│       │   │   ├── SlideItem.tsx     # 单个 Slide 卡片
│       │   │   └── SlideEditor.tsx   # Slide 编辑器
│       │   ├── preview/
│       │   │   ├── ImagePreview.tsx  # 图片预览区
│       │   │   └── ThumbnailBar.tsx  # 缩略图栏
│       │   ├── player/
│       │   │   └── FullscreenPlayer.tsx  # 全屏播放器
│       │   ├── style/
│       │   │   └── StylePickerModal.tsx  # 风格选择弹窗
│       │   └── common/
│       │       ├── Button.tsx
│       │       ├── Input.tsx
│       │       └── Modal.tsx
│       ├── hooks/                    # 自定义 Hooks
│       │   ├── useSlides.ts
│       │   └── useKeyboard.ts
│       ├── types/                    # TypeScript 类型定义
│       │   └── index.ts
│       └── styles/
│           └── globals.css
│
├── slides/                           # 数据存储目录
│   └── <slug>/
│       ├── outline.yml
│       └── images/
│           ├── style/                # 风格图片存储
│           │   └── <hash>.jpg
│           └── <sid>/
│               └── <blake3_hash>.jpg
│
├── pyproject.toml                    # Python 项目配置 (uv 管理)
├── uv.lock                           # uv 锁定文件
└── README.md
```

## 2. 后端架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                      API 层 (api/)                       │
│  - 处理 HTTP 请求/响应                                    │
│  - 参数验证 (Pydantic schemas)                           │
│  - 路由定义                                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    业务层 (services/)                    │
│  - 业务逻辑处理                                          │
│  - 调用外部服务 (Gemini API)                             │
│  - 编排多个 Repository 操作                              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   存储层 (repositories/)                 │
│  - 文件系统操作                                          │
│  - YAML 读写                                            │
│  - 图片文件管理                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心类设计

#### SlideRepository

```python
class SlideRepository:
    """Slide 数据存储层"""

    def __init__(self, base_path: str = "./slides"):
        self.base_path = Path(base_path)

    def get_project(self, slug: str) -> Optional[Project]
    def save_project(self, slug: str, project: Project) -> None
    def create_project(self, slug: str, title: str) -> Project
    def delete_project(self, slug: str) -> None
    def project_exists(self, slug: str) -> bool
```

#### ImageRepository

```python
class ImageRepository:
    """图片文件存储层"""

    def __init__(self, base_path: str = "./slides"):
        self.base_path = Path(base_path)

    def save_image(self, slug: str, sid: str, content_hash: str, image_data: bytes) -> str
    def get_image_path(self, slug: str, sid: str, content_hash: str) -> Optional[Path]
    def list_images(self, slug: str, sid: str) -> List[ImageInfo]
    def delete_image(self, slug: str, sid: str, content_hash: str) -> None
    def save_style_image(self, slug: str, image_data: bytes) -> str
    def get_style_image_path(self, slug: str, filename: str) -> Optional[Path]
```

#### SlideService

```python
class SlideService:
    """Slide 业务逻辑层"""

    def __init__(self, slide_repo: SlideRepository, image_repo: ImageRepository):
        self.slide_repo = slide_repo
        self.image_repo = image_repo

    def get_slides(self, slug: str) -> ProjectResponse
    def create_slide(self, slug: str, content: str, position: Optional[int]) -> Slide
    def update_slide(self, slug: str, sid: str, content: str) -> Slide
    def delete_slide(self, slug: str, sid: str) -> None
    def reorder_slides(self, slug: str, slide_ids: List[str]) -> List[Slide]
```

#### ImageService

```python
class ImageService:
    """图片生成业务逻辑层"""

    def __init__(self, gemini_client: GeminiClient, image_repo: ImageRepository, slide_repo: SlideRepository):
        self.gemini_client = gemini_client
        self.image_repo = image_repo
        self.slide_repo = slide_repo

    async def generate_image(self, slug: str, sid: str, prompt: str, style_image: Optional[str]) -> ImageInfo
    def get_slide_images(self, slug: str, sid: str) -> List[ImageInfo]
    def get_matching_image(self, slug: str, sid: str, content_hash: str) -> Optional[ImageInfo]
```

#### StyleService

```python
class StyleService:
    """风格管理业务逻辑层"""

    def __init__(self, gemini_client: GeminiClient, image_repo: ImageRepository, slide_repo: SlideRepository):
        self.gemini_client = gemini_client
        self.image_repo = image_repo
        self.slide_repo = slide_repo

    async def generate_style_candidates(self, slug: str, prompt: str) -> List[StyleCandidate]
    def select_style(self, slug: str, prompt: str, image_filename: str) -> Style
    def get_style(self, slug: str) -> Optional[Style]
```

## 3. API 接口设计

### 3.1 项目与 Slides 接口

#### GET /api/slides/{slug}

获取指定项目的所有 slides 信息。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**响应：**

```json
{
  "slug": "hello-world",
  "title": "Hello World 演示",
  "style": {
    "prompt": "水彩画风格，柔和的色调",
    "image": "style_abc123.jpg"
  },
  "slides": [
    {
      "sid": "slide_001",
      "content": "一只可爱的猫咪在阳光下打盹",
      "content_hash": "abc123def456",
      "created_at": "2024-01-11T10:00:00Z",
      "updated_at": "2024-01-11T10:30:00Z",
      "has_matching_image": true,
      "image_count": 3
    }
  ]
}
```

**错误响应：**
- `404 Not Found`: 项目不存在

---

#### POST /api/slides/{slug}

创建新的 slides 项目或在现有项目中添加新 slide。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**请求体：**

```json
{
  "title": "新项目标题",
  "content": "第一张 slide 的内容",
  "position": 0
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| title | string | 否 | 项目标题（仅创建新项目时需要） |
| content | string | 是 | Slide 文字内容 |
| position | integer | 否 | 插入位置（0-based），不传则追加到末尾 |

**响应：**

```json
{
  "sid": "slide_003",
  "content": "第一张 slide 的内容",
  "content_hash": "xyz789",
  "created_at": "2024-01-11T11:00:00Z",
  "updated_at": "2024-01-11T11:00:00Z",
  "has_matching_image": false,
  "image_count": 0
}
```

---

#### PUT /api/slides/{slug}/{sid}

更新指定 slide 的内容。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| sid | string | path | 是 | Slide ID |

**请求体：**

```json
{
  "content": "更新后的文字内容"
}
```

**响应：**

```json
{
  "sid": "slide_001",
  "content": "更新后的文字内容",
  "content_hash": "new_hash_456",
  "created_at": "2024-01-11T10:00:00Z",
  "updated_at": "2024-01-11T12:00:00Z",
  "has_matching_image": false,
  "image_count": 3
}
```

---

#### DELETE /api/slides/{slug}/{sid}

删除指定 slide。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| sid | string | path | 是 | Slide ID |

**响应：**

```json
{
  "success": true,
  "message": "Slide deleted successfully"
}
```

---

#### PUT /api/slides/{slug}/reorder

重新排序 slides。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**请求体：**

```json
{
  "slide_ids": ["slide_002", "slide_001", "slide_003"]
}
```

**响应：**

```json
{
  "success": true,
  "slides": [
    {"sid": "slide_002", "content": "..."},
    {"sid": "slide_001", "content": "..."},
    {"sid": "slide_003", "content": "..."}
  ]
}
```

---

#### PUT /api/slides/{slug}/title

更新项目标题。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**请求体：**

```json
{
  "title": "新的项目标题"
}
```

**响应：**

```json
{
  "success": true,
  "title": "新的项目标题"
}
```

---

### 3.2 图片接口

#### GET /api/slides/{slug}/{sid}/images

获取指定 slide 的所有图片。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| sid | string | path | 是 | Slide ID |

**响应：**

```json
{
  "sid": "slide_001",
  "current_content_hash": "abc123def456",
  "images": [
    {
      "filename": "abc123def456.jpg",
      "content_hash": "abc123def456",
      "url": "/api/slides/hello-world/slide_001/images/abc123def456.jpg",
      "is_current": true,
      "created_at": "2024-01-11T10:30:00Z"
    },
    {
      "filename": "old_hash_789.jpg",
      "content_hash": "old_hash_789",
      "url": "/api/slides/hello-world/slide_001/images/old_hash_789.jpg",
      "is_current": false,
      "created_at": "2024-01-11T10:00:00Z"
    }
  ]
}
```

---

#### GET /api/slides/{slug}/{sid}/images/{filename}

获取指定图片文件。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| sid | string | path | 是 | Slide ID |
| filename | string | path | 是 | 图片文件名 |

**响应：**
- Content-Type: image/jpeg
- 返回图片二进制数据

---

#### POST /api/slides/{slug}/{sid}/generate

为指定 slide 生成新图片。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| sid | string | path | 是 | Slide ID |

**请求体：**（可选）

```json
{
  "prompt_override": "可选的额外提示词"
}
```

**响应：**

```json
{
  "image": {
    "filename": "abc123def456.jpg",
    "content_hash": "abc123def456",
    "url": "/api/slides/hello-world/slide_001/images/abc123def456.jpg",
    "is_current": true,
    "created_at": "2024-01-11T12:00:00Z"
  },
  "generation_cost": 0.02
}
```

---

### 3.3 风格接口

#### GET /api/slides/{slug}/style

获取项目的风格设置。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**响应：**

```json
{
  "has_style": true,
  "style": {
    "prompt": "水彩画风格，柔和的色调",
    "image": "style_abc123.jpg",
    "image_url": "/api/slides/hello-world/style/style_abc123.jpg"
  }
}
```

若无风格设置：

```json
{
  "has_style": false,
  "style": null
}
```

---

#### POST /api/slides/{slug}/style/generate

根据提示词生成两张候选风格图片。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**请求体：**

```json
{
  "prompt": "水彩画风格，柔和的色调"
}
```

**响应：**

```json
{
  "candidates": [
    {
      "filename": "candidate_1_abc123.jpg",
      "url": "/api/slides/hello-world/style/candidate_1_abc123.jpg"
    },
    {
      "filename": "candidate_2_def456.jpg",
      "url": "/api/slides/hello-world/style/candidate_2_def456.jpg"
    }
  ],
  "generation_cost": 0.04
}
```

---

#### PUT /api/slides/{slug}/style

选择并保存风格。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**请求体：**

```json
{
  "prompt": "水彩画风格，柔和的色调",
  "selected_image": "candidate_1_abc123.jpg"
}
```

**响应：**

```json
{
  "success": true,
  "style": {
    "prompt": "水彩画风格，柔和的色调",
    "image": "style_abc123.jpg",
    "image_url": "/api/slides/hello-world/style/style_abc123.jpg"
  }
}
```

---

#### GET /api/slides/{slug}/style/{filename}

获取风格图片文件。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |
| filename | string | path | 是 | 图片文件名 |

**响应：**
- Content-Type: image/jpeg
- 返回图片二进制数据

---

### 3.4 成本接口

#### GET /api/cost/{slug}

获取项目的成本统计。

**请求参数：**
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| slug | string | path | 是 | 项目标识符 |

**响应：**

```json
{
  "slug": "hello-world",
  "total_cost": 0.56,
  "currency": "USD",
  "breakdown": {
    "slide_images": 0.48,
    "style_images": 0.08
  },
  "image_count": 24,
  "cost_per_image": 0.02
}
```

---

## 4. 数据模型

### 4.1 outline.yml 完整结构

```yaml
title: "项目标题"
style:
  prompt: "风格描述提示词"
  image: "style_abc123.jpg"
total_cost: 0.56                      # 累计成本
slides:
  - sid: "slide_001"
    content: "slide 文字内容"
    created_at: "2024-01-11T10:00:00Z"
    updated_at: "2024-01-11T10:30:00Z"
  - sid: "slide_002"
    content: "另一个 slide"
    created_at: "2024-01-11T10:05:00Z"
    updated_at: "2024-01-11T10:05:00Z"
```

### 4.2 领域模型

```python
# models/style.py
@dataclass
class Style:
    prompt: str
    image: str

# models/slide.py
@dataclass
class Slide:
    sid: str
    content: str
    created_at: datetime
    updated_at: datetime

    @property
    def content_hash(self) -> str:
        """基于 content 计算 blake3 hash"""
        return compute_blake3(self.content)

# models/project.py
@dataclass
class Project:
    title: str
    style: Optional[Style]
    slides: List[Slide]
    total_cost: float = 0.0
```

### 4.3 API Schema 模型

```python
# api/schemas/slide.py
class SlideResponse(BaseModel):
    sid: str
    content: str
    content_hash: str
    created_at: datetime
    updated_at: datetime
    has_matching_image: bool
    image_count: int

class CreateSlideRequest(BaseModel):
    title: Optional[str] = None
    content: str
    position: Optional[int] = None

class UpdateSlideRequest(BaseModel):
    content: str

class ReorderSlidesRequest(BaseModel):
    slide_ids: List[str]

# api/schemas/image.py
class ImageInfo(BaseModel):
    filename: str
    content_hash: str
    url: str
    is_current: bool
    created_at: datetime

class GenerateImageResponse(BaseModel):
    image: ImageInfo
    generation_cost: float

# api/schemas/style.py
class StyleCandidate(BaseModel):
    filename: str
    url: str

class GenerateStyleRequest(BaseModel):
    prompt: str

class GenerateStyleResponse(BaseModel):
    candidates: List[StyleCandidate]
    generation_cost: float

class SelectStyleRequest(BaseModel):
    prompt: str
    selected_image: str

class StyleResponse(BaseModel):
    prompt: str
    image: str
    image_url: str
```

## 5. 前端组件设计

### 5.1 状态管理 (Zustand Store)

```typescript
// stores/slideStore.ts
interface SlideState {
  // 数据
  slug: string | null;
  title: string;
  style: Style | null;
  slides: Slide[];
  selectedSlideId: string | null;
  currentImages: ImageInfo[];

  // 加载状态
  isLoading: boolean;
  isGenerating: boolean;

  // Actions
  loadProject: (slug: string) => Promise<void>;
  selectSlide: (sid: string) => void;
  createSlide: (content: string, position?: number) => Promise<void>;
  updateSlide: (sid: string, content: string) => Promise<void>;
  deleteSlide: (sid: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;
  updateTitle: (title: string) => Promise<void>;
  generateImage: (sid: string) => Promise<void>;
  loadSlideImages: (sid: string) => Promise<void>;
}

// stores/playerStore.ts
interface PlayerState {
  isPlaying: boolean;
  currentIndex: number;
  interval: number;

  startPlayback: (startIndex?: number) => void;
  stopPlayback: () => void;
  nextSlide: () => void;
  prevSlide: () => void;
  setInterval: (ms: number) => void;
}
```

### 5.2 核心组件

#### Header 组件

```
+------------------------------------------------------------------+
| [Logo] GenSlides    [ slides 题头输入框 ]           [$0.56] [播放] |
+------------------------------------------------------------------+
```

- Logo: 点击返回首页（可选）
- 题头输入框: 可编辑项目标题，失焦时自动保存
- 成本显示: 显示当前项目总成本
- 播放按钮: 进入全屏播放模式

#### SlideList 组件

- 支持拖拽排序 (react-dnd 或 @dnd-kit/core)
- 单击选中 slide
- 双击进入编辑模式
- 点击 slide 下方区域显示插入指示线

#### ImagePreview 组件

```
+------------------------------------------------+
|                                                |
|              [ 主图片展示区 ]                   |
|                                                |
+------------------------------------------------+
|         [ 生成新图片 ] (条件显示)               |
+------------------------------------------------+
|  [缩略图1] [缩略图2] [缩略图3] ...              |
+------------------------------------------------+
```

- 主区域展示当前选中的图片
- 若无匹配 hash 的图片，显示「生成新图片」按钮
- 底部缩略图栏可点击切换预览

#### StylePickerModal 组件

```
+------------------------------------------+
|           选择演示风格                     |
+------------------------------------------+
|                                          |
|  请输入风格描述:                          |
|  +------------------------------------+  |
|  | 水彩画风格，柔和的色调               |  |
|  +------------------------------------+  |
|                                          |
|            [ 生成风格图片 ]              |
|                                          |
|  +----------------+ +----------------+   |
|  |                | |                |   |
|  |   候选图片 1    | |   候选图片 2    |   |
|  |                | |                |   |
|  |   [ 选择 ]     | |   [ 选择 ]     |   |
|  +----------------+ +----------------+   |
|                                          |
+------------------------------------------+
```

- 首次打开项目时自动弹出（无 style 时）
- 输入提示词后生成两张候选图片
- 用户选择其中一张作为风格参考

#### FullscreenPlayer 组件

- 全屏展示当前 slide 图片
- 自动轮播（可配置间隔时间）
- 键盘控制：← → 切换，ESC 退出
- 底部进度指示器

### 5.3 API 封装

```typescript
// api/slides.ts
export const slidesApi = {
  getProject: (slug: string) => get<ProjectResponse>(`/api/slides/${slug}`),
  createSlide: (slug: string, data: CreateSlideRequest) =>
    post<SlideResponse>(`/api/slides/${slug}`, data),
  updateSlide: (slug: string, sid: string, data: UpdateSlideRequest) =>
    put<SlideResponse>(`/api/slides/${slug}/${sid}`, data),
  deleteSlide: (slug: string, sid: string) =>
    del(`/api/slides/${slug}/${sid}`),
  reorderSlides: (slug: string, slideIds: string[]) =>
    put(`/api/slides/${slug}/reorder`, { slide_ids: slideIds }),
  updateTitle: (slug: string, title: string) =>
    put(`/api/slides/${slug}/title`, { title }),
};

// api/images.ts
export const imagesApi = {
  getSlideImages: (slug: string, sid: string) =>
    get<SlideImagesResponse>(`/api/slides/${slug}/${sid}/images`),
  generateImage: (slug: string, sid: string) =>
    post<GenerateImageResponse>(`/api/slides/${slug}/${sid}/generate`),
  getImageUrl: (slug: string, sid: string, filename: string) =>
    `/api/slides/${slug}/${sid}/images/${filename}`,
};

// api/style.ts
export const styleApi = {
  getStyle: (slug: string) =>
    get<StyleResponse>(`/api/slides/${slug}/style`),
  generateStyleCandidates: (slug: string, prompt: string) =>
    post<GenerateStyleResponse>(`/api/slides/${slug}/style/generate`, { prompt }),
  selectStyle: (slug: string, prompt: string, selectedImage: string) =>
    put(`/api/slides/${slug}/style`, { prompt, selected_image: selectedImage }),
};
```

## 6. 技术实现要点

### 6.1 Blake3 哈希计算

```python
# utils/hash.py
import blake3

def compute_blake3(content: str) -> str:
    """计算字符串的 blake3 哈希值（前16位）"""
    return blake3.blake3(content.encode('utf-8')).hexdigest()[:16]
```

### 6.2 Gemini 图片生成

```python
# clients/gemini_client.py
from google import genai
from google.genai import types
from typing import Optional, List

class GeminiClient:
    """Google AI SDK (Gemini) 图片生成客户端"""

    MODEL_NAME = "gemini-3-pro-image-preview"  # 图片生成专用模型
    COST_PER_IMAGE = 0.134  # 单张图片生成成本

    def __init__(self, api_key: Optional[str] = None):
        # 如果提供 api_key 则使用，否则从环境变量读取
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()  # 使用 GOOGLE_API_KEY 环境变量

    async def generate_image(
        self,
        prompt: str,
        style_image: Optional[bytes] = None
    ) -> bytes:
        """
        生成图片，返回图片二进制数据 (PNG 格式)

        Args:
            prompt: 图片描述提示词
            style_image: 可选的风格参考图片（二进制数据）

        Returns:
            生成的图片二进制数据
        """
        contents = []

        if style_image:
            # 使用 Part.from_bytes 直接传递图片字节数据
            image_part = types.Part.from_bytes(data=style_image, mime_type="image/png")
            contents.append(image_part)
            contents.append(f"请参考上面图片的风格，生成以下内容：{prompt}")
        else:
            contents.append(prompt)

        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="2K",
                )
            ),
        )

        # 从响应中提取图片（直接获取原始字节数据）
        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        raise ValueError("No image generated in response")

    async def generate_style_candidates(
        self,
        prompt: str,
        count: int = 2
    ) -> List[bytes]:
        """
        生成风格候选图片

        Args:
            prompt: 风格描述提示词
            count: 生成图片数量（默认2张）

        Returns:
            生成的图片二进制数据列表
        """
        candidates = []
        style_prompt = f"生成一张展示「{prompt}」风格的示例图片，用于作为后续图片生成的风格参考"

        for i in range(count):
            varied_prompt = f"{style_prompt}（变体 {i + 1}）"

            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=[varied_prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9",
                        image_size="2K",
                    )
                ),
            )

            for part in response.parts:
                if part.inline_data is not None:
                    # 直接获取原始字节数据
                    candidates.append(part.inline_data.data)
                    break

        return candidates
```

**依赖安装：**

```bash
uv add google-genai
```

### 6.3 前端拖拽排序

使用 `@dnd-kit/core` 实现：

```typescript
// components/slides/SlideList.tsx
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';

function SlideList() {
  const { slides, reorderSlides } = useSlideStore();

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = slides.findIndex(s => s.sid === active.id);
      const newIndex = slides.findIndex(s => s.sid === over.id);
      const newOrder = arrayMove(slides, oldIndex, newIndex).map(s => s.sid);
      reorderSlides(newOrder);
    }
  };

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={slides.map(s => s.sid)} strategy={verticalListSortingStrategy}>
        {slides.map(slide => (
          <SortableSlideItem key={slide.sid} slide={slide} />
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

### 6.4 全屏播放

```typescript
// components/player/FullscreenPlayer.tsx
function FullscreenPlayer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { isPlaying, currentIndex, nextSlide, prevSlide, stopPlayback } = usePlayerStore();

  useEffect(() => {
    if (isPlaying) {
      containerRef.current?.requestFullscreen();
    }
  }, [isPlaying]);

  useKeyboard({
    ArrowRight: nextSlide,
    ArrowLeft: prevSlide,
    Escape: stopPlayback,
  });

  // ...
}
```

## 7. 配置管理

### 7.1 后端配置

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    slides_base_path: str = "./slides"
    host: str = "0.0.0.0"
    port: int = 3003
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### 7.2 环境变量

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
SLIDES_BASE_PATH=./slides
PORT=3003
```

### 7.3 路由注册顺序

由于多个路由模块共用 `/api/slides` 前缀，且存在模式匹配冲突（如 `/{slug}/{sid}` 会匹配 `/{slug}/style`），需要按照**特殊性从高到低**的顺序注册路由：

```python
# main.py - 路由注册顺序很重要！
# 1. style 路由：/{slug}/style/... 最具体
app.include_router(style.router)
# 2. images 路由：/{slug}/{sid}/images/... 次具体
app.include_router(images.router)
# 3. cost 路由：/cost/{slug} 独立路径
app.include_router(cost.router)
# 4. slides 路由：/{slug}/{sid} 最通用，必须最后注册
app.include_router(slides.router)
```

**注意**：如果顺序错误，`POST /api/slides/{slug}/style/generate` 会被 `PUT /api/slides/{slug}/{sid}` 错误匹配。

---

## 8. 项目初始化与运行

### 8.1 后端初始化

```bash
# 创建项目
uv init backend
cd backend

# 添加依赖
uv add fastapi uvicorn google-genai blake3 pyyaml pydantic-settings python-multipart

# 添加开发依赖
uv add --dev pytest pytest-asyncio httpx ruff

# 运行开发服务器
uv run uvicorn main:app --reload --port 3003
```

### 8.2 前端初始化

```bash
# 创建 Vite + React + TypeScript 项目
npm create vite@latest frontend -- --template react-ts
cd frontend

# 安装依赖
npm install zustand @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 运行开发服务器
npm run dev
```

### 8.3 pyproject.toml 示例

```toml
[project]
name = "genslides-backend"
version = "0.1.0"
description = "GenSlides - AI 图片幻灯片生成器后端"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.40.0",
    "google-genai>=1.56.0",
    "blake3>=1.0.8",
    "pyyaml>=6.0.3",
    "pydantic-settings>=2.12.0",
    "python-multipart>=0.0.20",
]

[tool.uv]
dev-dependencies = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "httpx>=0.28.1",
    "ruff>=0.14.11",
]

[tool.ruff]
line-length = 100
target-version = "py311"
```
