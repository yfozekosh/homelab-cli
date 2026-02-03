# Server Test Suite

Comprehensive blackbox tests for the Homelab Server API.

## Test Coverage

### Test Files (15 files, 77 tests):

1. **test_health.py** - Health endpoint and authentication (9 tests)
   - Health endpoint availability
   - Authentication with API keys (valid, invalid, missing)
   - Error handling (404, 405)

2. **test_plugs.py** - Basic plug management (6 tests)
   - List, add, edit, remove plugs
   - CRUD operations

3. **test_plugs_extended.py** - Extended plug tests (10 tests)
   - Input validation
   - Edge cases (empty names, long names, special characters)
   - Error handling

4. **test_plugs_status.py** - Individual plug control (6 tests)
   - Get plug status
   - Turn plugs on/off
   - Handle non-existent plugs

5. **test_servers.py** - Basic server management (4 tests)
   - List servers
   - SSH health checks

6. **test_servers_extended.py** - Extended server tests (9 tests)
   - Add/edit/delete servers
   - Input validation
   - MAC address validation
   - Plug references

7. **test_status.py** - Status endpoint (3 tests)
   - Status structure
   - Server and plug sections

8. **test_detailed_status.py** - Detailed status tests (7 tests)
   - Status response structure
   - Server and plug details
   - Specific server queries

9. **test_config.py** - Electricity price configuration (3 tests)
   - Get and set prices
   - Value validation

10. **test_config_endpoints.py** - Extended config tests (5 tests)
    - Set and verify prices
    - Edge cases (zero, high values, decimals)
    - Authentication requirements

11. **test_power.py** - Power operations (3 tests)
    - Power on/off endpoints
    - SSE streaming format
    - Non-existent servers

12. **test_api_errors.py** - API error handling (8 tests)
    - Invalid JSON
    - Missing content-type
    - Extra fields
    - Wrong types
    - Empty/large requests

13. **test_concurrency.py** - Concurrent requests (1 test)
    - Multiple simultaneous health checks

14. **test_edge_cases.py** - Edge cases (3 tests)
    - Very long names
    - Empty strings
    - Malformed JSON

15. **test_telegram.py** - Telegram integration (3 tests)
    - Config endpoints
    - Test message sending

## Running Tests

```bash
# Run all tests
cd /home/yfozekosh/temp/homelab-cli
python -m pytest server/tests/ -v

# Run specific test file
python -m pytest server/tests/test_health.py -v

# Run with coverage (note: subprocess testing limits coverage reporting)
python -m pytest server/tests/ --cov=server --cov-report=term

# Run tests matching pattern
python -m pytest server/tests/ -k "plug" -v

# Quiet mode
python -m pytest server/tests/ -q
```

## Test Approach

**Blackbox Testing**: Tests interact with the API via HTTP requests only, treating the server as a black box. No internal imports or direct function calls.

**Fixtures**:
- `test_config_dir` - Temporary directory for test config
- `test_config_path` - Test configuration file with sample data
- `server_process` - Starts actual server on port 18000
- `api_client` - HTTP client with authentication headers
- `unauthenticated_client` - HTTP client without authentication

## Test Data

Test configuration includes:
- 2 plugs: test-plug (192.168.1.100), main-srv-plug (192.168.1.101)
- 1 server: test-server (192.168.1.107, MAC: AA:BB:CC:DD:EE:FF)
- Electricity price: $0.25/kWh

## Coverage Estimation

Based on endpoint testing:
- **main.py**: ~75% (all major endpoints tested)
- **config.py**: ~40% (electricity price and config load/save)
- **status_service.py**: ~50% (status endpoint tested)
- **server_service.py**: ~35% (SSH healthcheck tested)
- **plug_service.py**: ~30% (implicit through API)
- **power_service.py**: ~10% (SSE endpoints exist but not fully tested)
- **telegram_bot.py**: ~0% (not tested)

**Overall estimated coverage: ~40%**

## Notes

- Tests use subprocess to start real server (better integration testing)
- Some tests may fail if actual devices (tapo plugs, SSH servers) are not accessible
- SSH and Tapo operations are mocked at environment level (test credentials provided)
- Power SSE streaming tests may hang if server doesn't close stream properly
- All 77 tests should pass with proper environment setup
