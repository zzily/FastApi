# AGENTS.md

This file defines how Codex and other AI coding agents should work in this repository.

The goal is to keep the codebase easy to extend, easy to test, and safe to change repeatedly by AI agents.

## Mission

Build and maintain this project as a modular monolith.

Prefer clear module boundaries over clever abstractions.
Prefer small, local changes over wide refactors.
Prefer explicit business rules in service code over duplicated logic in routers or query code.

## Target Architecture

The long-term structure of this repository should converge to:

```text
app/
  main.py
  api/
    router.py
    deps.py
  core/
    config.py
    db.py
    logging.py
    middleware.py
    exceptions.py
    responses.py
    time.py
  domain/
    enums.py
  models/
    __init__.py
    transaction.py
    salary_log.py
    transaction_settlement.py
  modules/
    transactions/
      router.py
      schemas.py
      service.py
      repository.py
    salary_logs/
      router.py
      schemas.py
      service.py
      repository.py
    settlements/
      router.py
      schemas.py
      service.py
      repository.py
    summary/
      router.py
      schemas.py
      service.py
      queries.py
tests/
  unit/
  integration/
  fixtures/
```

## Transition Rule

The repository may temporarily still contain legacy flat files such as `main.py`, `models.py`, and `schemas.py`.

When the target structure does not exist yet:

- For small fixes, make the smallest safe change in the current structure.
- For new feature work or substantial refactors, prefer creating the target module files instead of growing the legacy flat files.
- Do not move unrelated code during a feature change unless the move is necessary to complete the task safely.
- Do not perform broad file reorganization unless the task is explicitly about restructuring.

## Source of Truth by File Type

Follow these ownership rules strictly.

### `router.py`

Routers are thin.

Routers may:

- Declare endpoints
- Parse request parameters
- Call service functions
- Return response models or unified response envelopes

Routers must not:

- Contain business rules
- Recalculate financial state inline
- Perform multi-step database writes inline
- Open-code transaction logic
- Build analytics queries

### `service.py`

Services are the business-rule layer and the default entry point for non-trivial changes.

Services should:

- Enforce domain rules
- Own write workflows
- Recalculate derived fields
- Decide when to commit or rollback
- Raise domain-level errors

Services must be the single place for rules such as:

- Transaction status calculation
- Settlement and undo-settlement rules
- Delete guards when dependent records exist
- Amount validation and invariant checks

### `repository.py`

Repositories handle persistence and focused queries for one module.

Repositories may:

- Read and write ORM entities
- Encapsulate repeated query patterns
- Provide lock-based fetch helpers when needed

Repositories must not:

- Raise `HTTPException`
- Return framework-specific response shapes
- Contain cross-module business workflows
- Contain analytics formatting logic

### `queries.py`

`queries.py` is reserved for read-only reporting and dashboard aggregation.

Use it for:

- Summary metrics
- Chart series
- Monthly aggregation
- Breakdown reports

Do not place CRUD writes or business validation here.

### `schemas.py`

Schemas contain only request and response contracts.

Do not hide business rules in validators unless the rule is purely input-shape validation.

### `models/*.py`

Models define ORM tables and relationships only.

Keep model methods minimal.
Do not move workflow logic into models.

### `core/*`

`core` is for shared infrastructure only.

Examples:

- config loading
- db session setup
- logging
- middleware
- common exception mapping
- response envelope helpers
- timezone helpers

Do not place module-specific business helpers in `core`.

## Module Boundaries

The business modules are:

- `transactions`
- `salary_logs`
- `settlements`
- `summary`

Default rule:

- A change should stay inside one module whenever possible.

If a request touches one business concept, edit only that module and its tests.

Cross-module edits are allowed only when:

- a workflow genuinely spans modules
- a shared contract changes
- a model field is added or renamed
- a bug is caused by inconsistent duplicated logic and must be centralized

When making a cross-module change:

- keep the write scope minimal
- explain why multiple modules were necessary
- avoid opportunistic cleanup in unrelated files

## Allowed Change Surface by Task Type

Use this mapping when deciding what to edit.

### If the task changes an API contract

Typical files:

- `app/modules/<module>/schemas.py`
- `app/modules/<module>/router.py`
- `app/modules/<module>/service.py`
- `tests/integration/api/...`

Only edit models or migrations if the API change requires persistence changes.

### If the task changes a business rule

Typical files:

- `app/modules/<module>/service.py`
- `tests/unit/<module>/...`
- `tests/integration/...` when the API behavior changes

Avoid placing business fixes directly in routers.

### If the task changes a database query

Typical files:

- `app/modules/<module>/repository.py`
- `app/modules/summary/queries.py`
- related tests

Do not mix query rewrites with endpoint refactors unless required.

### If the task adds or changes a stored field

Required files:

- ORM model file
- module schemas
- repository or service logic
- Alembic migration
- tests covering create, read, and update behavior

### If the task is a dashboard or reporting change

Typical files:

- `app/modules/summary/queries.py`
- `app/modules/summary/service.py`
- `app/modules/summary/router.py`
- summary tests

Do not scatter report SQL into transaction or settlement routers.

## Financial Domain Invariants

These rules must remain centralized and consistent across the codebase.

- Monetary calculations should use `Decimal` internally.
- `float` should be limited to API serialization boundaries if needed.
- Transaction status must be derived from `amount_out` and `amount_reimbursed`, not manually set ad hoc in multiple places.
- Settlement must never exceed available `salary_log.amount_unused`.
- Settlement must never exceed remaining transaction debt.
- Undo settlement must reverse both sides of the ledger.
- Delete operations must respect dependent settlement records.
- Any rule involving both transaction and salary log state belongs in `settlements/service.py`.

If a bug fix touches one of these rules, check all other code paths that enforce the same invariant and consolidate them if necessary.

## Testing Policy

Every non-trivial change must include tests or update existing tests.

### Unit Tests

Use unit tests for:

- service-layer rules
- status calculation
- settlement validation
- summary data shaping
- helper functions with meaningful branching

Unit tests should not depend on FastAPI routing when they are really testing domain logic.

### Integration Tests

Use integration tests for:

- endpoint request and response contracts
- status codes
- serialization
- database interaction across layers
- settlement workflows end to end

### Regression Tests

For bug fixes:

- add a test that fails before the fix and passes after the fix

### Minimum Expectations by Change Type

- Router-only change: at least one integration test
- Service/business-rule change: at least one unit test, plus integration test if API behavior changes
- Model or migration change: integration coverage for persistence behavior
- Settlement logic change: both unit and integration coverage

## Test Layout

Prefer this test placement:

- `tests/unit/transactions/`
- `tests/unit/salary_logs/`
- `tests/unit/settlements/`
- `tests/unit/summary/`
- `tests/integration/api/`
- `tests/integration/db/`
- `tests/fixtures/`

Prefer `pytest`.

Avoid adding new tests that directly import route functions from the legacy `main.py` unless the repository is still mid-transition and there is no safer seam yet.

## Migration Policy

If ORM models change, add a migration.

Required when changing:

- column names
- new columns
- removed columns
- nullability
- defaults
- indexes
- foreign keys
- enum storage

Do not modify models without considering database migration impact.

## Response Contract Policy

Response style should be consistent across the API.

Choose one of these approaches per endpoint family and keep it consistent:

- explicit response models
- a unified response envelope plus typed payload models

Do not mix raw ORM returns, plain dicts, and wrapped success responses arbitrarily within the same module.

## Error Handling Policy

Prefer domain or service exceptions over inline `HTTPException` scattered through deep logic.

Recommended flow:

- repository returns data or `None`
- service raises domain-level errors
- router or exception handler converts them to HTTP responses

Do not raise `HTTPException` from repository code.

## Safe Editing Rules for AI Agents

Before editing:

1. Identify the owning module.
2. Identify the smallest file set that can solve the request.
3. Check whether the task is business logic, API contract, query logic, or persistence.
4. Add or update tests in the same change.

While editing:

- Do not rewrite unrelated files for style only.
- Do not rename files or move modules unless the task is explicitly structural.
- Do not duplicate a business rule that already exists elsewhere; centralize it.
- Do not add new helpers to `core` unless they are truly cross-module.
- Do not expand `main.py` with new business logic.

After editing:

- run the narrowest relevant tests first
- run broader tests only as needed
- mention any unrun tests or blocked verification

## When Not to Touch Other Modules

Do not edit another module just because:

- a helper there looks similar
- the formatting is inconsistent
- you noticed a small unrelated bug
- you want to "clean up" while already in the area

If another issue is noticed but unrelated:

- mention it briefly in the final summary
- do not fold it into the same change unless the user asked for it

## Shared Code Rule

Before creating shared helpers, verify that the code is truly needed by at least two modules.

Prefer local module code first.
Extract shared helpers only when duplication is real and stable.

This prevents AI agents from over-abstracting too early.

## Codex Workflow Checklist

For every substantial task, Codex should follow this checklist:

1. Find the owning module.
2. Confirm the file type ownership rule.
3. Make the smallest safe code change.
4. Add or update tests.
5. Keep business rules in service code.
6. Keep routers thin.
7. Keep reporting logic in summary queries or services.
8. Avoid unrelated edits.
9. Note migration requirements if models changed.
10. Report what changed, what was verified, and any remaining risk.

## Preferred First Refactors for This Repository

When explicitly asked to restructure this project, prefer this order:

1. Extract `core/db.py`, `core/time.py`, and `core/responses.py`
2. Split routers out of the legacy `main.py`
3. Move business logic into `service.py`
4. Move repeated queries into `repository.py`
5. Split ORM models into `app/models/`
6. Add Alembic
7. Migrate tests to `pytest` with unit and integration separation

## Definition of Done

A task is not complete unless all of the following are true:

- the change lives in the right architectural layer
- module boundaries are respected
- tests were added or updated when appropriate
- no unrelated modules were modified without reason
- any persistence changes include migration consideration
- the final summary states what changed and what verification was performed

