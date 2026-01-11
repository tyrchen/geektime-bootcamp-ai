# Code Review Prompts Library

A collection of specialized prompts for different code review scenarios with Codex CLI.

## General Purpose Reviews

### Comprehensive Code Review

```
Review the code in [FILES/DIRECTORY]. Provide a thorough analysis covering:

## Summary
Brief overview of what the code does and its purpose.

## Code Quality
- Readability and clarity
- Naming conventions
- Code organization
- DRY principle adherence
- SOLID principles compliance

## Correctness
- Logic errors
- Edge cases not handled
- Off-by-one errors
- Null/undefined handling
- Type safety issues

## Security
- Input validation
- Authentication/authorization
- Data sanitization
- Injection vulnerabilities
- Sensitive data handling

## Performance
- Algorithm efficiency
- Resource management
- Caching opportunities
- Unnecessary operations

## Maintainability
- Test coverage gaps
- Documentation needs
- Complexity hotspots
- Refactoring opportunities

Rate each finding: Critical / High / Medium / Low / Info
Provide specific file:line references and fix suggestions.
```

### Quick Review

```
Quick review of [FILES]. Focus only on:
1. Bugs that would cause runtime errors
2. Security vulnerabilities
3. Critical performance issues

Skip style and minor improvements. Be concise.
```

## Language-Specific Reviews

### TypeScript/JavaScript Review

```
Review [FILES] with TypeScript/JavaScript best practices:

**Type Safety:**
- Missing or weak types (any, unknown usage)
- Type assertions that could fail
- Generic type opportunities

**Async Patterns:**
- Unhandled promise rejections
- Race conditions
- Missing error boundaries
- Callback hell / promise chains

**Modern JS:**
- Optional chaining opportunities
- Nullish coalescing usage
- Destructuring improvements
- Array methods vs loops

**React-Specific (if applicable):**
- Unnecessary re-renders
- Missing dependencies in hooks
- Prop drilling issues
- State management concerns
```

### Python Review

```
Review [FILES] following Python best practices:

**Pythonic Code:**
- List comprehension opportunities
- Context manager usage (with statements)
- Generator expressions
- f-string formatting

**Type Hints:**
- Missing type annotations
- Incorrect type hints
- Optional vs Union usage

**Error Handling:**
- Bare except clauses
- Swallowed exceptions
- Missing finally blocks

**Performance:**
- Global variable abuse
- Inefficient string concatenation
- Missing __slots__
- Generator vs list when iterating once
```

### Go Review

```
Review [FILES] for Go idioms and best practices:

**Error Handling:**
- Unchecked errors
- Error wrapping
- Sentinel errors vs error types

**Concurrency:**
- Goroutine leaks
- Channel deadlocks
- Race conditions
- Context propagation

**Interfaces:**
- Interface segregation
- Accepting interfaces, returning structs
- Empty interface usage

**Memory:**
- Slice capacity hints
- String builders for concatenation
- Pointer vs value receivers
```

### Rust Review

```
Review [FILES] for Rust best practices:

**Ownership:**
- Unnecessary cloning
- Borrow checker workarounds
- Lifetime annotations

**Error Handling:**
- Unwrap/expect in production code
- Custom error types
- Result/Option usage

**Performance:**
- Unnecessary allocations
- Iterator vs loop
- Cow usage opportunities

**Safety:**
- Unsafe block justification
- Panic potential
- Thread safety (Send/Sync)
```

## Security-Focused Reviews

### Web Application Security Audit

```
Perform a security audit of [FILES/DIRECTORY]:

**Authentication:**
- Credential handling
- Session management
- Token validation
- Password policies

**Authorization:**
- Access control checks
- Privilege escalation paths
- IDOR vulnerabilities

**Input Validation:**
- SQL injection (parameterized queries)
- XSS (output encoding)
- Command injection
- Path traversal
- SSRF potential

**Data Protection:**
- Sensitive data in logs
- Encryption at rest/transit
- PII handling
- Secure headers

**Dependencies:**
- Known vulnerabilities
- Outdated packages
- Unnecessary dependencies

For each finding, provide:
- CVSS-like severity (Critical/High/Medium/Low)
- Attack scenario
- Remediation with code example
```

### API Security Review

```
Review API code in [FILES] for security:

**Authentication:**
- API key handling
- JWT validation
- OAuth implementation

**Rate Limiting:**
- Missing rate limits
- Bypass potential
- Resource exhaustion

**Input:**
- Request validation
- Content-type enforcement
- Size limits

**Output:**
- Error message information leakage
- Stack trace exposure
- Verbose error responses

**CORS:**
- Overly permissive origins
- Credential handling
- Preflight caching
```

## Performance Reviews

### Database Performance Review

```
Review database operations in [FILES]:

**Query Efficiency:**
- N+1 query patterns
- Missing indexes (suggest based on queries)
- Unnecessary JOINs
- SELECT * usage

**Connection Management:**
- Connection pooling
- Connection leaks
- Transaction scope

**Caching:**
- Cacheable queries
- Cache invalidation
- Read replica opportunities

**Data Access Patterns:**
- Batch operations
- Pagination implementation
- Large result set handling
```

### Frontend Performance Review

```
Review frontend code in [FILES]:

**Rendering:**
- Unnecessary re-renders
- Virtual DOM thrashing
- Layout thrashing
- Paint optimization

**Loading:**
- Bundle size impact
- Code splitting opportunities
- Lazy loading candidates
- Preloading strategies

**Runtime:**
- Memory leaks (event listeners)
- Expensive computations in render
- Debounce/throttle needs
- Web worker candidates

**Network:**
- Request waterfall issues
- Caching headers
- Compression
- Image optimization
```

## Architecture Reviews

### Microservice Architecture Review

```
Review [SERVICE_FILES] for microservice best practices:

**Service Boundaries:**
- Single responsibility
- Domain alignment
- Data ownership

**Communication:**
- Sync vs async appropriateness
- Circuit breaker patterns
- Retry policies
- Timeout handling

**Resilience:**
- Fallback strategies
- Graceful degradation
- Health checks
- Idempotency

**Observability:**
- Logging correlation
- Metrics exposure
- Distributed tracing
- Alert thresholds
```

### API Design Review

```
Review API design in [FILES]:

**RESTful Principles:**
- Resource naming
- HTTP method usage
- Status code selection
- HATEOAS compliance

**Consistency:**
- Naming conventions
- Error response format
- Pagination pattern
- Filtering/sorting

**Versioning:**
- Version strategy
- Breaking change handling
- Deprecation approach

**Documentation:**
- OpenAPI/Swagger completeness
- Example requests/responses
- Error documentation
```

## PR Review Templates

### Feature PR Review

```
Review this feature PR:

**Functionality:**
- [ ] Implements requirements correctly
- [ ] Handles edge cases
- [ ] Error handling complete

**Code Quality:**
- [ ] Follows project conventions
- [ ] No code duplication
- [ ] Appropriate abstractions

**Testing:**
- [ ] Unit tests added
- [ ] Integration tests if needed
- [ ] Edge cases covered

**Documentation:**
- [ ] README updated if needed
- [ ] API docs updated
- [ ] Code comments where complex

**Security:**
- [ ] No new vulnerabilities
- [ ] Input validation present
- [ ] Secrets handling correct

VERDICT: [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]

Required Changes:
[List blocking issues]

Suggestions:
[List non-blocking improvements]
```

### Bug Fix PR Review

```
Review this bug fix PR:

**Root Cause:**
- Is the actual bug correctly identified?
- Is this the right place to fix it?
- Are there related bugs?

**Fix Quality:**
- Does it fix the bug without side effects?
- Is it the minimal change needed?
- Could it cause regressions?

**Testing:**
- Is there a test that would have caught this?
- Is there a test that prevents regression?

**Documentation:**
- Should the changelog be updated?
- Are there related docs to update?

VERDICT: [APPROVE / REQUEST_CHANGES]
```

## Specialized Reviews

### Migration Review

```
Review this migration/upgrade in [FILES]:

**Backwards Compatibility:**
- Breaking changes identified
- Migration path documented
- Rollback strategy

**Data Integrity:**
- Data transformation correctness
- Null handling
- Default values

**Performance:**
- Migration duration estimate
- Lock implications
- Batch processing

**Testing:**
- Dry-run capability
- Verification steps
- Rollback testing
```

### Configuration Review

```
Review configuration in [FILES]:

**Security:**
- Secrets in config (should be env vars)
- Default credentials
- Overly permissive settings

**Environment Handling:**
- Environment-specific overrides
- Default values appropriateness
- Validation of required values

**Maintainability:**
- Documentation of options
- Sensible defaults
- Clear naming
```
