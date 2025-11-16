# API Testing with REST Client

This directory contains REST Client test files for testing the Database Query Tool API.

## Prerequisites

1. Install the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension in VSCode
2. Ensure the backend server is running (`make dev-backend` or `make dev`)

## Usage

1. Open `test.rest` in VSCode
2. Click the "Send Request" link above each HTTP request
3. View the response in the VSCode panel

## Variables

The test file uses variables that you can customize:

- `@baseUrl`: API base URL (default: `http://localhost:8000/api/v1`)
- `@dbName`: Database connection name for testing (default: `testdb`)
- `@testDbUrl`: PostgreSQL connection URL (default: `postgresql://postgres:postgres@localhost:5432/testdb`)

## Test Scenarios

The file includes tests for:

1. **Health Check** - Verify backend is running
2. **Database Management** - CRUD operations for database connections
3. **Metadata Operations** - Get and refresh database metadata
4. **SQL Query Execution** - Various SELECT queries
5. **Natural Language to SQL** - LLM-powered SQL generation
6. **Query History** - Retrieve execution history
7. **Error Cases** - Validation and error handling
8. **Edge Cases** - Special characters, NULL handling, complex queries

## Running Tests

### Individual Tests
Click "Send Request" above any request to execute it individually.

### Complete Workflow
Follow the numbered requests in order to test a complete workflow:
1. Add database connection
2. Get metadata
3. Execute queries
4. Check history

## Notes

- Make sure your PostgreSQL database is running and accessible
- Update `@testDbUrl` if your database credentials differ
- Some tests require a database with specific tables (users, orders, etc.)
- Error tests are expected to fail - they verify error handling
