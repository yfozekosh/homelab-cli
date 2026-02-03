#!/bin/bash
# Quick test runner script

echo "======================================"
echo "Homelab Test Suite"
echo "======================================"
echo ""

# Fast tests (no hardware)
echo "Running fast tests (client + non-hardware server tests)..."
pytest client/tests/ server/tests/test_health.py server/tests/test_plugs.py server/tests/test_servers.py server/tests/test_config*.py server/tests/test_api_errors.py -q

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
