#!/bin/bash
# Manual Test Commands for Camera Registration Endpoint
# Run these commands one at a time to test

echo "=========================================="
echo "TEST 1: Health Check"
echo "=========================================="
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
echo ""

echo "=========================================="
echo "TEST 2: Register New Camera (camera_1)"
echo "=========================================="
curl -s -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "camera_1",
    "name": "Front Door",
    "location": "Main Entrance",
    "ip_address": "192.168.1.201"
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "TEST 3: Re-register Same Camera (update)"
echo "=========================================="
curl -s -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "camera_1",
    "name": "Front Door UPDATED",
    "location": "Main Entrance",
    "ip_address": "192.168.1.202"
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "TEST 4: Register All 4 Cameras"
echo "=========================================="
for i in 1 2 3 4; do
  echo "Registering camera_$i..."
  curl -s -X POST http://localhost:8000/api/v1/cameras/register \
    -H "Content-Type: application/json" \
    -d "{
      \"camera_id\": \"camera_$i\",
      \"name\": \"Camera $i\",
      \"location\": \"Location $i\",
      \"ip_address\": \"192.168.1.20$i\"
    }" | python3 -m json.tool
  echo ""
done

echo "=========================================="
echo "TEST 5: Validation Error - Missing Field"
echo "=========================================="
curl -s -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "invalid_camera"
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "TEST 6: Validation Error - Invalid Format"
echo "=========================================="
curl -s -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "camera-with-hyphens",
    "name": "Invalid",
    "location": "Test",
    "ip_address": "192.168.1.1"
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "TEST 7: Check Database"
echo "=========================================="
echo "Run this command to see cameras in database:"
echo "mysql -u securitycam -p security_cameras -e 'SELECT * FROM cameras;'"
