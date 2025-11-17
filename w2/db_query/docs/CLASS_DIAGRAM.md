# Class Diagram and Relationships

## UML Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        <<interface>>                             │
│                      DatabaseAdapter                             │
├─────────────────────────────────────────────────────────────────┤
│ # config: ConnectionConfig                                       │
│ # _pool: Optional[Any]                                           │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: ConnectionConfig)                             │
│ + test_connection(): Tuple[bool, Optional[str]]                  │
│ + get_connection_pool(): Any                                     │
│ + close_connection_pool(): None                                  │
│ + extract_metadata(): MetadataResult                             │
│ + execute_query(sql: str): QueryResult                           │
│ + get_dialect_name(): str                                        │
│ + get_identifier_quote_char(): str                               │
└─────────────────────────────────────────────────────────────────┘
                               △
                               │ implements
                ┌──────────────┼──────────────┐
                │              │              │
┌───────────────┴────────┐ ┌──┴────────────┐ ┌┴──────────────────┐
│  PostgreSQLAdapter     │ │  MySQLAdapter │ │  OracleAdapter    │
├────────────────────────┤ ├───────────────┤ ├───────────────────┤
│ - _pool: asyncpg.Pool  │ │ - _pool: Pool │ │ - _pool: Pool     │
├────────────────────────┤ ├───────────────┤ ├───────────────────┤
│ + All abstract methods │ │ + All methods │ │ + All methods     │
│ - _parse_url()         │ │ - _parse_url()│ │ - _parse_url()    │
│ - _get_columns()       │ │ - _get_tables()│ │ - _extract_meta() │
│ - _get_row_count()     │ │ - _map_type() │ │ - _map_type()     │
│ - _infer_type()        │ │ - _infer_type()│ │ - _infer_type()   │
└────────────────────────┘ └───────────────┘ └───────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│               DatabaseAdapterRegistry                            │
├─────────────────────────────────────────────────────────────────┤
│ - _adapters: Dict[DatabaseType, Type[DatabaseAdapter]]          │
│ - _instances: Dict[str, DatabaseAdapter]                        │
├─────────────────────────────────────────────────────────────────┤
│ + __init__()                                                     │
│ + register(type, adapter_class): None                            │
│ + get_adapter(type, config): DatabaseAdapter                    │
│ + close_adapter(type, name): None                               │
│ + close_all_adapters(): None                                    │
│ + is_supported(type): bool                                       │
│ + get_supported_types(): List[DatabaseType]                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ creates and manages
                               ▼
                       DatabaseAdapter


┌─────────────────────────────────────────────────────────────────┐
│                    DatabaseService                               │
├─────────────────────────────────────────────────────────────────┤
│ - registry: DatabaseAdapterRegistry                              │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(registry: DatabaseAdapterRegistry)                    │
│ + test_connection(type, url): Tuple[bool, str]                  │
│ + execute_query(type, name, url, sql): Tuple[Result, int]       │
│ + extract_metadata(type, name, url): MetadataResult             │
│ + close_connection(type, name): None                            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ uses
                               ▼
                  DatabaseAdapterRegistry


┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Router                             │
│                    (queries.py, databases.py)                    │
├─────────────────────────────────────────────────────────────────┤
│ + POST   /api/v1/dbs/{name}/query                               │
│ + POST   /api/v1/dbs/{name}/query/natural                       │
│ + GET    /api/v1/dbs/{name}/history                             │
│ + GET    /api/v1/dbs/{name}                                     │
│ + POST   /api/v1/dbs/{name}/refresh                             │
│ + PUT    /api/v1/dbs/{name}                                     │
│ + DELETE /api/v1/dbs/{name}                                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ depends on
                               ▼
                       DatabaseService
```

## Data Classes

```
┌─────────────────────────────────────────────────────────────────┐
│                      ConnectionConfig                            │
├─────────────────────────────────────────────────────────────────┤
│ + url: str                                                       │
│ + name: str                                                      │
│ + min_pool_size: int = 1                                         │
│ + max_pool_size: int = 5                                         │
│ + command_timeout: int = 60                                      │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                        QueryResult                               │
├─────────────────────────────────────────────────────────────────┤
│ + columns: List[Dict[str, str]]                                  │
│ + rows: List[Dict[str, Any]]                                     │
│ + row_count: int                                                 │
├─────────────────────────────────────────────────────────────────┤
│ + to_dict(): Dict[str, Any]                                      │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      MetadataResult                              │
├─────────────────────────────────────────────────────────────────┤
│ + tables: List[Dict[str, Any]]                                   │
│ + views: List[Dict[str, Any]]                                    │
├─────────────────────────────────────────────────────────────────┤
│ + to_dict(): Dict[str, Any]                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Sequence Diagrams

### Query Execution Flow

```
Client          API Router      DatabaseService    Registry         Adapter
  │                 │                  │               │               │
  │  POST /query    │                  │               │               │
  ├────────────────>│                  │               │               │
  │                 │                  │               │               │
  │                 │ execute_query()  │               │               │
  │                 ├─────────────────>│               │               │
  │                 │                  │               │               │
  │                 │                  │ get_adapter() │               │
  │                 │                  ├──────────────>│               │
  │                 │                  │               │               │
  │                 │                  │               │ [create if    │
  │                 │                  │               │  not exists]  │
  │                 │                  │               │               │
  │                 │                  │<──────────────┤               │
  │                 │                  │  adapter      │               │
  │                 │                  │               │               │
  │                 │                  │ validate_sql()│               │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │ execute_query(sql)            │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │               │  get_pool()   │
  │                 │                  │               │  execute SQL  │
  │                 │                  │               │               │
  │                 │                  │<──────────────┼───────────────┤
  │                 │                  │   QueryResult │               │
  │                 │<─────────────────┤               │               │
  │                 │  result, time    │               │               │
  │                 │                  │               │               │
  │                 │ save_history()   │               │               │
  │                 │                  │               │               │
  │<────────────────┤                  │               │               │
  │  JSON response  │                  │               │               │
  │                 │                  │               │               │
```

### Metadata Extraction Flow

```
Client          API Router      DatabaseService    Registry         Adapter
  │                 │                  │               │               │
  │  GET /{name}    │                  │               │               │
  ├────────────────>│                  │               │               │
  │                 │                  │               │               │
  │                 │ extract_metadata()│              │               │
  │                 ├─────────────────>│               │               │
  │                 │                  │               │               │
  │                 │                  │ get_adapter() │               │
  │                 │                  ├──────────────>│               │
  │                 │                  │<──────────────┤               │
  │                 │                  │  adapter      │               │
  │                 │                  │               │               │
  │                 │                  │ extract_metadata()            │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │               │  query catalog│
  │                 │                  │               │  build result │
  │                 │                  │               │               │
  │                 │                  │<──────────────┼───────────────┤
  │                 │                  │ MetadataResult│               │
  │                 │<─────────────────┤               │               │
  │                 │  metadata        │               │               │
  │                 │                  │               │               │
  │                 │ cache_metadata() │               │               │
  │                 │                  │               │               │
  │<────────────────┤                  │               │               │
  │  JSON response  │                  │               │               │
  │                 │                  │               │               │
```

### Adapter Registration Flow

```
Application    Registry         PostgreSQLAdapter    MySQLAdapter
  Startup         │                     │                  │
     │            │                     │                  │
     │ __init__() │                     │                  │
     ├───────────>│                     │                  │
     │            │                     │                  │
     │            │ register(POSTGRESQL, PostgreSQLAdapter)│
     │            ├────────────────────>│                  │
     │            │    [store mapping]  │                  │
     │            │                     │                  │
     │            │ register(MYSQL, MySQLAdapter)          │
     │            ├────────────────────────────────────────>│
     │            │    [store mapping]  │                  │
     │            │                     │                  │
     │<───────────┤                     │                  │
     │  registry  │                     │                  │
     │            │                     │                  │
     │            │                     │                  │
   [ready]        │                     │                  │
```

## Dependency Graph

```
                                    Application
                                         │
                                         ▼
                                    main.py
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
             API Layer          DatabaseService      AdapterRegistry
          (databases.py,             │                      │
           queries.py)               │                      │
                    │                │                      │
                    └────────────────┼──────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            SQLValidator      QueryHistory      Adapters
                                              (PostgreSQL,
                                               MySQL, etc.)
                                                     │
                                                     ▼
                                            Database Drivers
                                            (asyncpg, aiomysql)
```

## Object Lifecycle

### Adapter Instance Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│  1. Creation                                                  │
│     config = ConnectionConfig(url=..., name="mydb")          │
│     adapter = PostgreSQLAdapter(config)                      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  2. Registration (cached in registry)                         │
│     registry._instances["postgresql:mydb"] = adapter         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  3. Connection Pool Creation (lazy)                           │
│     pool = await adapter.get_connection_pool()              │
│     # Creates pool on first call, returns cached on next     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  4. Usage (multiple queries)                                  │
│     result1 = await adapter.execute_query("SELECT...")       │
│     result2 = await adapter.execute_query("SELECT...")       │
│     # Reuses same pool                                       │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  5. Cleanup                                                   │
│     await registry.close_adapter(db_type, name)              │
│     # Closes pool, removes from registry                     │
└──────────────────────────────────────────────────────────────┘
```

## Design Patterns Used

### 1. Abstract Factory Pattern
```
DatabaseAdapterRegistry creates DatabaseAdapter instances
based on DatabaseType
```

### 2. Factory Method Pattern
```
Each adapter implements factory methods:
- get_connection_pool() creates database-specific pools
```

### 3. Facade Pattern
```
DatabaseService provides simplified interface to:
- Adapter registry
- SQL validation
- Query execution
- Metadata extraction
```

### 4. Singleton Pattern
```
Global instances:
- adapter_registry
- database_service
```

### 5. Strategy Pattern
```
Different adapters implement different strategies for:
- Connection management
- Metadata extraction
- Query execution
```

### 6. Template Method Pattern
```
DatabaseAdapter defines template:
1. Get pool
2. Acquire connection
3. Execute operation
4. Process results
5. Return standardized format
```

## Relationship Types

### Inheritance
```
PostgreSQLAdapter ──▷ DatabaseAdapter (is-a)
MySQLAdapter ──▷ DatabaseAdapter (is-a)
```

### Composition
```
DatabaseService ◆── DatabaseAdapterRegistry (has-a)
DatabaseAdapter ◆── ConnectionConfig (has-a)
```

### Dependency
```
DatabaseService ···> DatabaseAdapter (uses)
API Router ···> DatabaseService (uses)
```

### Association
```
DatabaseAdapterRegistry ──> DatabaseAdapter (creates)
```

## SOLID Principles Mapping

### Single Responsibility
- **DatabaseAdapter**: Database operations
- **DatabaseAdapterRegistry**: Adapter lifecycle
- **DatabaseService**: Business logic coordination
- **API Router**: HTTP request/response

### Open-Closed
- **Open**: Add new adapters by creating new classes
- **Closed**: Existing adapters don't need modification

### Liskov Substitution
- All adapters can substitute DatabaseAdapter

### Interface Segregation
- DatabaseAdapter has focused interface
- No adapter forced to implement unused methods

### Dependency Inversion
- High-level (Service) depends on abstraction (DatabaseAdapter)
- Low-level (adapters) implement abstraction
- Not dependent on concrete implementations
