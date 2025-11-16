# Instructions

## constitution

这是针对 ./w2/db_query 项目的:

- 后端使用 Ergonomic Python 风格来编写代码，前端使用 typescript
- 前后端都要有严格的类型标注
- 使用 pydantic 来定义数据模型
- 所有后端生成的 JSON 数据，使用 camelCase 格式。
- 不需要 authentication，任何用户都可以使用。

## 基本思路

这是一个数据库查询工具，用户可以添加一个 db url，系统会连接到数据库，获取数据库的 metadta，然后将数据库中的 table 和 view 的信息展示出来，然后用户可以自己输入 sql 查询，也可以通过自然语言来生成 sql 查询。

基本想法：

- 数据库连接字符串和数据库的 metadata 都会存储到 sqlite 数据库中。我们可以根据 postgres 的功能来查询系统中的表和视图的信息，然后用 LLM 来将这些信息转换成 json 格式，然后存储到 sqlite 数据库中。这个信息以后可以复用。
- 当用户使用 LLM 来生成 sql 查询时，我们可以把系统中的表和视图的信息作为 context 传递给 LLM，然后 LLM 会根据这些信息来生成 sql 查询。
- 任何输入的 sql 语句，都需要经过 sqlparser 解析，确保语法正确，并且仅包含 select 语句。如果语法不正确，需要给出错误信息。
  - 如果查询不包含 limit 子句，则默认添加 limit 1000 子句。
- 输出格式是 json，前端将其组织成表格，并显示出来。

后端使用 Python (uv) / FastAPI / sqlglot / openai sdk 来实现。
前端使用 React / refine 5 / tailwind / ant design 来实现。sql editor 使用 monaco editor 来实现。

OpenAI API key 在环境变量 OPENAI_API_KEY 中。数据库连接和 metadata 存储在 sqlite 数据库中，放在 ~/.db_query/db_query.db 中。

后端 API 需要支持 cors，允许所有 origin。大致 API 如下：

```bash
# 获取所有已存储的数据库
GET /api/v1/dbs
# 添加一个数据库
PUT /api/v1/dbs/{name}

{
  "url": "postgres://postgres:postgres@localhost:5432/postgres"
}

# 获取一个数据库的 metadata
GET /api/v1/dbs/{name}

# 查询某个数据库的信息
POST /api/v1/dbs/{name}/query

{
  "sql": "SELECT * FROM users"
}

# 根据自然语言生成 sql
POST /api/v1/dbs/{name}/query/natural

{
  "prompt": "查询用户表的所有信息"
}
```

## 测试

仔细阅读 ./w2/db_query 下面的代码，然后运行后端和前端，根据@w2/db_query/fixtures/test.rest 用 curl 测试后端已实现的路由；然后用 playwright 开前端进行测试，任何测试问题，think ultra hard and fix

## db migration & unit test

`make setup` 会出错，修复它；确保前后端 unit test 都通过。
