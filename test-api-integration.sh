#!/bin/bash

# Test API Integration Script
# Verifies that Python BMS API and Node.js server are properly connected

echo "=== API Integration Test ==="

# Test 1: Check if Python BMS API is running
echo "Test 1: Checking Python BMS API (port 8000)..."
if curl -s http://localhost:8000/api/batteries > /dev/null; then
    echo "✓ Python BMS API is accessible"
    echo "Sample response:"
    curl -s http://localhost:8000/api/batteries | jq '.[0:2]' || curl -s http://localhost:8000/api/batteries
else
    echo "✗ Python BMS API is not accessible at http://localhost:8000"
    echo "Make sure dual_bms_service.py is running"
fi

echo ""

# Test 2: Check if Node.js UI server is running
echo "Test 2: Checking Node.js UI server (port 3000)..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Node.js UI server is accessible"
else
    echo "✗ Node.js UI server is not accessible at http://localhost:3000"
    echo "Make sure the UI service is running"
fi

echo ""

# Test 3: Check if Node.js server can proxy BMS data
echo "Test 3: Checking Node.js server BMS proxy..."
if curl -s http://localhost:3000/api/batteries > /dev/null; then
    echo "✓ Node.js server can proxy BMS data"
    echo "Sample response:"
    curl -s http://localhost:3000/api/batteries | jq '.[0:2]' || curl -s http://localhost:3000/api/batteries
else
    echo "✗ Node.js server cannot proxy BMS data"
    echo "Check server logs for errors"
fi

echo ""

# Test 4: Check BMS status endpoint
echo "Test 4: Checking BMS status endpoint..."
if curl -s http://localhost:3000/api/bms/status > /dev/null; then
    echo "✓ BMS status endpoint is working"
    echo "Status response:"
    curl -s http://localhost:3000/api/bms/status | jq '.' || curl -s http://localhost:3000/api/bms/status
else
    echo "✗ BMS status endpoint is not working"
fi

echo ""

# Test 5: Check service status
echo "Test 5: Checking systemd services..."
echo "j5-bms-api: $(systemctl is-active j5-bms-api 2>/dev/null || echo 'not found')"
echo "j5-ui: $(systemctl is-active j5-ui 2>/dev/null || echo 'not found')"
echo "j5-kiosk: $(systemctl is-active j5-kiosk 2>/dev/null || echo 'not found')"

echo ""
echo "=== Test Complete ==="
echo ""
echo "If any tests failed, check:"
echo "1. Python BMS service: sudo journalctl -u j5-bms-api -f"
echo "2. Node.js UI service: sudo journalctl -u j5-ui -f"
echo "3. Manual start: python3 dual_bms_service.py"
echo "4. Manual start: npm run start"
