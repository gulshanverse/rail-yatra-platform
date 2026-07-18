# Technical Debt Register

This register details tracked technical debt, code deprecations, and architectural recommendations for the Phase 5 system.

---

## 1. Tracked Technical Debt Items

### Item 1: Python Deprecation warnings for `datetime.utcnow()`
- **Evidence**: Pytest logs output 90+ `DeprecationWarning` flags:
  `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).`
- **Severity**: Low
- **Impact**: Potential breaking changes when migrating to future Python versions (Python 3.12+).
- **Recommendation**: Refactor calls using `datetime.utcnow()` to use timezone-aware UTC datetime wrappers.
- **Estimated Effort**: 2-3 hours
- **Priority**: Medium

---

## 2. Code Smells and Architectural Assessment

- **Dead Code**: Verified no dead code or unused imports remain (Ruff check ensures unused imports are pruned).
- **Duplicate Logic**: The tie-breaking logic and risk score algorithms are fully modularized and reside in their respective packages, avoiding code cloning.
- **Coupling & Cohesion**: All subpackages display high cohesion (focused on a single domain capability) and loose coupling (communicating through ABC contracts).
- **Temporary Implementation**: All repository interfaces have clean in-memory mock databases. In production, these should be backed by permanent PostgreSQL or Redis adapters. (Effort: High, Priority: Low/Deferred).
