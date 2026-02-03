# Test Performance Notes

## Issue: Status Tests are Slow

Status-related tests take significantly longer than other tests due to hardware queries.

### Root Cause

The `/status` endpoint queries actual Tapo smart plugs via network:
1. Connects to each plug's IP address
2. Queries device info (power, energy, state)
3. Network timeouts occur when devices are unreachable

### Timing Breakdown

| Test Category | Tests | Time | Per Test |
|---------------|-------|------|----------|
| Health, Auth, Errors | 9 | 0.8s | 0.09s |
| Plugs (CRUD only) | 6 | 0.2s | 0.03s |
| Config | 3 | 0.2s | 0.07s |
| **Status (with hardware)** | 3 | 13s | 4.3s |
| Plug Status (hardware) | 6 | ~18s | 3s |

### Mitigations Applied

1. **Added Timeouts** to all Tapo operations (1.5s per call)
   - Before: 5-10s default TCP timeout
   - After: 1.5s explicit timeout
   - Result: ~50% faster

2. **Error Handling** returns offline status on timeout
   - Tests don't fail on unreachable hardware
   - Status returns gracefully degraded data

### Current Performance

- **Fast tests** (no hardware): 18 tests in 0.8s (45ms/test)
- **Status tests** (hardware queries): 3 tests in 13s (4.3s/test)
- **Full suite** (92 tests): ~60-90 seconds

### Recommendations

For faster CI/CD pipelines:

**Option 1: Skip hardware tests**
```bash
pytest server/tests/ -m "not hardware"
```

**Option 2: Mock Tapo client**
```python
@pytest.fixture
def mock_tapo(monkeypatch):
    # Mock ApiClient to return fake data
    pass
```

**Option 3: Separate test suites**
- Unit tests: Fast, no hardware (< 5s)
- Integration tests: With hardware (slower, optional)

## Why Not Mock Everything?

Current approach (real server + real endpoints) provides:
- ✅ True integration testing
- ✅ Catches real networking issues
- ✅ Validates actual API behavior
- ✅ Tests production code paths

Trade-off: Slower tests but higher confidence in production readiness.

## Test Execution Strategy

```bash
# Fast feedback loop (development)
pytest server/tests/test_health.py server/tests/test_plugs.py server/tests/test_config.py

# Full validation (pre-commit)
pytest server/tests/ -x  # Stop on first failure

# CI/CD
pytest server/tests/ --tb=short --maxfail=3
```
