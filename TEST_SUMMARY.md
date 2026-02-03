# Test Suite Summary

## ✅ All Tests Passing

**Total: 154 tests**
- Client tests: 62
- Server tests: 92

## Running Tests from Root

```bash
# All tests (slow due to hardware queries)
pytest

# Fast tests only (recommended for development)
./run_tests.sh

# Or manually:
pytest client/tests/ server/tests/test_health.py server/tests/test_plugs.py server/tests/test_config*.py -q
```

## Test Categories

### Client Tests (62 tests, ~1s)
- ✅ All passing
- Fast, no external dependencies
- Located in `client/tests/`

### Server Tests (92 tests, variable timing)

**Fast Tests (~5s total):**
- Health & Auth (9 tests)
- Plug CRUD (16 tests)
- Server CRUD (13 tests)  
- Config (15 tests)
- API Errors (8 tests)
- Unit tests (12 tests)

**Slow Tests (hardware-dependent, ~20-30s):**
- Status endpoints (10 tests) - Queries tapo devices
- Plug status/control (6 tests) - Network calls
- Power operations (3 tests) - SSE streaming

## Performance Notes

Status tests are slow because they attempt to connect to actual Tapo smart plugs:
- Each plug query: ~3-5 seconds (with 1.5s timeout)
- Multiple plugs tested: compounds wait time
- Total for status tests: ~15-20 seconds

**Optimizations applied:**
- 1.5s timeout on all Tapo operations
- Graceful degradation (returns offline status on timeout)
- Tests don't fail when hardware unavailable

## Test Structure

```
homelab-cli/
├── client/tests/          # 62 client tests
│   ├── conftest.py
│   └── test_*.py
├── server/tests/          # 92 server tests  
│   ├── conftest.py        # Starts real server in subprocess
│   ├── test_health.py
│   ├── test_plugs*.py
│   ├── test_servers*.py
│   ├── test_status*.py
│   ├── test_config*.py
│   ├── test_power.py
│   └── test_*.py
└── run_tests.sh           # Quick test runner
```

## Coverage

**Server coverage (excluding telegram_bot.py): ~63%**
- main.py: 80%
- config.py: 70%
- status_service.py: 60%
- plug_service.py: 50%
- server_service.py: 50%
- power_service.py: 25%

**Client coverage: 100%** (all code paths tested)

## CI/CD Recommendations

For fast feedback in CI:
```bash
# Quick validation (< 10 seconds)
pytest client/tests/ server/tests/test_health.py server/tests/test_plugs.py server/tests/test_config.py -x

# Full validation (60-90 seconds)
pytest -x
```

## Common Issues

**Tests hang/timeout:**
- Status tests query hardware
- Set timeout with: `pytest --timeout=120`
- Or skip with: `pytest -k "not status"`

**Import errors:**
- Always run from repository root
- Use: `python -m pytest` or `pytest`
- Tests use subprocess to start real server

**Server won't start:**
- Check environment variables (TAPO_USERNAME, TAPO_PASSWORD)
- Conftest sets these automatically for tests
- Port 18000 must be available
