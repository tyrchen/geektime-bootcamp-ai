# Tasks: 数据库查询工具

**Input**: Design documents from `/specs/001-db-query-tool/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `w2/db_query/backend/` and `w2/db_query/frontend/`

---

## Phase 1: Setup & Foundation

**Purpose**: Project initialization and core infrastructure that blocks all features

### Backend Setup

- [X] T001 Create backend project structure at w2/db_query/backend/
- [X] T002 Initialize Python project with uv (pyproject.toml) at w2/db_query/backend/pyproject.toml
- [X] T003 [P] Create .python-version file specifying Python 3.12 at w2/db_query/backend/.python-version
- [X] T004 [P] Add backend dependencies (FastAPI, Pydantic v2, sqlglot, OpenAI SDK, asyncpg, SQLModel, pytest) to pyproject.toml
- [X] T005 [P] Create .env.example file with OPENAI_API_KEY template at w2/db_query/backend/.env.example
- [X] T006 [P] Create .gitignore for Python at w2/db_query/backend/.gitignore

### Frontend Setup

- [X] T007 Create frontend project structure at w2/db_query/frontend/
- [X] T008 Initialize Vite + React + TypeScript project at w2/db_query/frontend/
- [X] T009 [P] Add frontend dependencies (React 19, Refine 5, Ant Design 5, Monaco Editor, Tailwind CSS 4) to package.json
- [X] T010 [P] Configure TypeScript with strict mode in tsconfig.json at w2/db_query/frontend/tsconfig.json
- [X] T011 [P] Configure Tailwind CSS in tailwind.config.js at w2/db_query/frontend/tailwind.config.js
- [X] T012 [P] Create .env.local.example with VITE_API_BASE_URL at w2/db_query/frontend/.env.local.example
- [X] T013 [P] Create .gitignore for Node.js at w2/db_query/frontend/.gitignore

### Core Backend Infrastructure

- [X] T014 Create FastAPI application entry point in w2/db_query/backend/app/main.py
- [X] T015 Configure CORS middleware for all origins in w2/db_query/backend/app/main.py
- [X] T016 Create Pydantic Settings configuration in w2/db_query/backend/app/config.py
- [X] T017 Setup SQLite database connection and session in w2/db_query/backend/app/database.py
- [X] T018 Create Alembic migrations configuration in w2/db_query/backend/alembic.ini
- [X] T019 Create initial database schema migration in w2/db_query/backend/alembic/versions/001_initial_schema.py

### Core Data Models

- [X] T020 [P] Create DatabaseConnection SQLModel in w2/db_query/backend/app/models/database.py
- [X] T021 [P] Create DatabaseMetadata SQLModel in w2/db_query/backend/app/models/metadata.py
- [X] T022 [P] Create QueryHistory SQLModel in w2/db_query/backend/app/models/query.py
- [X] T023 [P] Create API request/response schemas (camelCase) in w2/db_query/backend/app/models/schemas.py
- [X] T024 Configure Pydantic alias_generator for camelCase globally in w2/db_query/backend/app/models/**init**.py

**Checkpoint**: Foundation ready - backend can start, database schema created, models defined

---

## Phase 2: Core Features (US1 + US2)

**Goal**: MVP功能 - 用户可以添加数据库连接、查看元数据、执行SQL查询

**Independent Test**: 添加PostgreSQL连接 → 查看表结构 → 执行SELECT查询 → 看到结果表格

### US1: Database Connection Management (P1 - MVP Core)

#### Backend Services - US1

- [X] T025 [P] [US1] Implement SQL validator service using sqlglot in w2/db_query/backend/app/services/sql_validator.py
- [X] T026 [P] [US1] Implement database connection service (test connection, asyncpg pool) in w2/db_query/backend/app/services/db_connection.py
- [X] T027 [US1] Implement metadata extraction service (query pg_catalog) in w2/db_query/backend/app/services/metadata.py
- [X] T028 [US1] Implement metadata caching logic in w2/db_query/backend/app/services/metadata.py

#### Backend API - US1

- [X] T029 [US1] Create databases router in w2/db_query/backend/app/api/v1/databases.py
- [X] T030 [US1] Implement PUT /api/v1/dbs/{name} endpoint (create/update connection) in databases.py
- [X] T031 [US1] Implement GET /api/v1/dbs endpoint (list all connections) in databases.py
- [X] T032 [US1] Implement GET /api/v1/dbs/{name} endpoint (get metadata) in databases.py
- [X] T033 [US1] Implement DELETE /api/v1/dbs/{name} endpoint in databases.py
- [X] T034 [US1] Implement POST /api/v1/dbs/{name}/refresh endpoint in databases.py

#### Frontend Types & Services - US1

- [X] T035 [P] [US1] Create TypeScript types for database connection in w2/db_query/frontend/src/types/database.ts
- [X] T036 [P] [US1] Create TypeScript types for metadata in w2/db_query/frontend/src/types/metadata.ts
- [X] T037 [US1] Create Axios API client instance in w2/db_query/frontend/src/services/api.ts
- [X] T038 [US1] Create Refine data provider in w2/db_query/frontend/src/services/dataProvider.ts

#### Frontend Pages - US1

- [X] T039 [US1] Setup Refine app with Ant Design in w2/db_query/frontend/src/App.tsx
- [X] T040 [US1] Create database list page in w2/db_query/frontend/src/pages/databases/list.tsx
- [X] T041 [US1] Create database create/edit form page in w2/db_query/frontend/src/pages/databases/create.tsx
- [X] T042 [US1] Create metadata tree view component in w2/db_query/frontend/src/components/MetadataTree.tsx
- [X] T043 [US1] Create database detail page (show metadata) in w2/db_query/frontend/src/pages/databases/show.tsx

**Checkpoint US1**: Users can add PostgreSQL connections and view table/column metadata

---

### US2: SQL Query Execution (P2 - Core Query)

#### Backend Services - US2

- [X] T044 [US2] Implement query execution service (asyncpg execute) in w2/db_query/backend/app/services/query.py
- [X] T045 [US2] Implement query history management in w2/db_query/backend/app/services/query.py
- [X] T046 [US2] Add SQL validation (SELECT only) and LIMIT injection logic in sql_validator.py

#### Backend API - US2

- [X] T047 [US2] Create queries router in w2/db_query/backend/app/api/v1/queries.py
- [X] T048 [US2] Implement POST /api/v1/dbs/{name}/query endpoint in queries.py
- [X] T049 [US2] Implement GET /api/v1/dbs/{name}/history endpoint in queries.py
- [X] T050 [US2] Add error handling for SQL validation errors in queries.py

#### Frontend Types & Components - US2

- [X] T051 [P] [US2] Create TypeScript types for query result in w2/db_query/frontend/src/types/query.ts
- [X] T052 [US2] Create Monaco-based SQL editor component in w2/db_query/frontend/src/components/SqlEditor.tsx
- [X] T053 [US2] Configure Monaco editor for SQL syntax highlighting and autocomplete in SqlEditor.tsx
- [X] T054 [US2] Create query result table component in w2/db_query/frontend/src/components/ResultTable.tsx
- [X] T055 [US2] Add pagination support to result table in ResultTable.tsx

#### Frontend Pages - US2

- [X] T056 [US2] Create query execution page in w2/db_query/frontend/src/pages/queries/execute.tsx
- [X] T057 [US2] Integrate SQL editor and result table in execute.tsx
- [X] T058 [US2] Add query history panel in execute.tsx
- [X] T059 [US2] Add loading state and error display in execute.tsx

**Checkpoint US2**: Users can write SQL, execute queries, view results in table, see query history

**🎯 MVP Complete**: At this point, the tool is fully functional for core use cases

---

## Phase 3: Enhanced Features (US3 + US4)

**Goal**: 增强功能 - 自然语言生成SQL和结果导出

**Independent Test**: US3 输入自然语言 → 生成SQL → 执行 | US4 导出查询结果为CSV/JSON

### US3: Natural Language to SQL (P3 - AI Enhancement)

#### Backend Services - US3

- [X] T060 [US3] Implement OpenAI client wrapper in w2/db_query/backend/app/services/nl2sql.py
- [X] T061 [US3] Create prompt template with metadata context in nl2sql.py
- [X] T062 [US3] Implement natural language to SQL conversion in nl2sql.py
- [X] T063 [US3] Add error handling for LLM API failures in nl2sql.py

#### Backend API - US3

- [X] T064 [US3] Implement POST /api/v1/dbs/{name}/query/natural endpoint in w2/db_query/backend/app/api/v1/queries.py
- [ ] T065 [US3] Add rate limiting for LLM endpoint (optional) in queries.py

#### Frontend Components - US3

- [X] T066 [US3] Create natural language input component in w2/db_query/frontend/src/components/NaturalLanguageInput.tsx
- [X] T067 [US3] Add tab switcher (Manual SQL / Natural Language) to query page
- [X] T068 [US3] Integrate natural language input in w2/db_query/frontend/src/pages/Home.tsx
- [X] T069 [US3] Display generated SQL in editor with edit capability in Home.tsx

**Checkpoint US3**: Users can generate SQL from Chinese/English natural language

---

### US4: Query Result Export (P4 - Convenience)

#### Backend Services - US4

- [X] T070 [P] [US4] Implement CSV export service in w2/db_query/backend/app/services/export.py
- [X] T071 [P] [US4] Implement JSON export service in export.py

#### Backend API - US4

- [ ] T072 [US4] Implement GET /api/v1/dbs/{name}/query/export endpoint in w2/db_query/backend/app/api/v1/queries.py (NOTE: Frontend implements client-side export instead)
- [ ] T073 [US4] Add query parameters for format selection (csv/json) in queries.py (NOTE: Not needed for client-side export)

#### Frontend Components - US4

- [X] T074 [US4] Implement CSV export in Home.tsx with handleExportCSV
- [X] T075 [US4] Implement JSON export in Home.tsx with handleExportJSON
- [X] T076 [US4] Implement file download logic with timestamp naming in Home.tsx
- [X] T077 [US4] Add large result set warning (>10000 rows) in Home.tsx

**Checkpoint US4**: Users can export query results to CSV and JSON files

---

## Phase 4: Polish & Documentation

**Purpose**: Production readiness and developer experience

### Documentation

- [ ] T078 [P] Create backend README.md with setup instructions at w2/db_query/backend/README.md
- [ ] T079 [P] Create frontend README.md with setup instructions at w2/db_query/frontend/README.md
- [ ] T080 [P] Create root README.md with project overview at w2/db_query/README.md
- [ ] T081 [P] Add API usage examples to backend README

### Testing & Quality

- [ ] T082 [P] Add unit tests for SQL validator in w2/db_query/backend/tests/unit/test_sql_validator.py
- [ ] T083 [P] Add integration tests for database API in w2/db_query/backend/tests/integration/test_api_databases.py
- [ ] T084 [P] Add integration tests for query API in w2/db_query/backend/tests/integration/test_api_queries.py
- [ ] T085 [P] Add contract tests for camelCase format in w2/db_query/backend/tests/contract/test_api_contracts.py

### Developer Tools

- [ ] T086 [P] Setup ruff configuration for backend linting at w2/db_query/backend/ruff.toml
- [ ] T087 [P] Setup ESLint configuration for frontend at w2/db_query/frontend/eslint.config.js
- [ ] T088 [P] Create start script for both backend and frontend at w2/db_query/start.sh

**Checkpoint**: Project is fully documented, tested, and ready for use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup & Foundation)**: No dependencies - start here
- **Phase 2 (Core Features)**: Depends on Phase 1 completion - ALL foundation must be ready
- **Phase 3 (Enhanced Features)**: Depends on Phase 2 completion - Core features must work
- **Phase 4 (Polish)**: Can run in parallel with Phase 3 or after Phase 3

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 1 foundation
- **US2 (P2)**: Depends on US1 (needs database connections and metadata)
- **US3 (P3)**: Depends on US2 (uses query execution infrastructure)
- **US4 (P4)**: Depends on US2 (exports query results)

### Critical Path

```
Phase 1 (Setup) → US1 (Connections) → US2 (Queries) → US3 (NL2SQL)
                                                      → US4 (Export)
                                                      → Phase 4 (Polish)
```

### Parallel Opportunities

**Within Phase 1**:

- Backend and Frontend setup can proceed in parallel (T001-T006 || T007-T013)
- Data models can be created in parallel (T020-T024)

**Within Phase 2**:

- Backend services for US1 can be created in parallel (T025-T026)
- Frontend types can be created in parallel (T035-T036)

**Within Phase 3**:

- US3 and US4 can be implemented in parallel (different features)
- Backend and frontend work within each story can overlap

**Within Phase 4**:

- All documentation and testing tasks can run in parallel (T078-T088)

---

## Implementation Strategy

### MVP First (Phases 1 + 2)

1. Complete Phase 1: Setup & Foundation (T001-T024)
2. Complete US1: Database Connections (T025-T043)
3. Complete US2: Query Execution (T044-T059)
4. **STOP and VALIDATE**: Test complete workflow end-to-end
5. Deploy/demo if ready

**Estimated MVP Tasks**: 59 tasks
**Estimated MVP Time**: 2-3 days for experienced developer

### Incremental Delivery

1. Phase 1 → Foundation ready → Validate backend starts
2. Phase 1 + US1 → Can manage connections → Test with real database
3. Phase 1 + US1 + US2 → Full MVP → Production ready for basic use
4. Add US3 → NL2SQL capability → Enhanced UX
5. Add US4 → Export capability → Complete feature set
6. Phase 4 → Polished product → Documentation and tests complete

### Parallel Team Strategy

With 2 developers:

1. **Developer A**: Backend (T001-T006, T014-T024, T025-T034, T044-T050, T060-T065, T070-T073)
2. **Developer B**: Frontend (T007-T013, T035-T043, T051-T059, T066-T069, T074-T077)
3. Both can work in parallel after Phase 1 foundation is complete

---

## Task Summary

**Total Tasks**: 88

**By Phase**:

- Phase 1 (Setup & Foundation): 24 tasks
- Phase 2 (Core Features - US1 + US2): 35 tasks (19 for US1, 16 for US2)
- Phase 3 (Enhanced Features - US3 + US4): 18 tasks (10 for US3, 8 for US4)
- Phase 4 (Polish & Documentation): 11 tasks

**By Component**:

- Backend: ~45 tasks
- Frontend: ~35 tasks
- Documentation/Testing: ~8 tasks

**Parallelizable Tasks**: 28 tasks marked with [P]

**Critical Path Tasks** (blocking others): ~30 tasks

---

## Notes

- All tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- Tasks are organized to enable independent implementation of user stories
- MVP can be achieved by completing Phases 1-2 only (59 tasks)
- Each user story is independently testable at its checkpoint
- Parallel opportunities are clearly marked with [P]
- File paths are explicit for every implementation task
- Tests are not included by default (can be added if requested)

---

**Ready for Implementation**: Use `/speckit.implement` to start executing tasks phase by phase.
