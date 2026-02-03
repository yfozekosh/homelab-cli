#!/bin/bash
# Quick test runner script

echo "======================================"
echo "Homelab Test Suite"
echo "======================================"
echo ""

# Fast tests (no hardware)
echo "Running fast tests (client + non-hardware server tests)..."
pytest client/tests/ server/tests/test_health.py server/tests/test_plugs.py server/tests/test_servers.py server/tests/test_config*.py server/tests/test_api_errors.py server/tests/test_detailed_status.py server/tests/test_edge_cases.py server/tests/test_concurrency.py server/tests/test_schemas.py server/tests/test_dependencies.py server/tests/test_constants.py server/tests/test_server_service.py server/tests/test_plug_service.py --cov=client --cov=server --cov-report=term-missing --cov-report=html --cov-report=xml -q

echo ""
echo "======================================"
echo "Fast tests complete!"
echo ""
echo "To run ALL tests (includes slow hardware queries):"
echo "  pytest"
echo ""
echo "To run only server tests:"
echo "  pytest server/tests/"
echo ""
echo "To run only client tests:"
echo "  pytest client/tests/"
echo "======================================"
