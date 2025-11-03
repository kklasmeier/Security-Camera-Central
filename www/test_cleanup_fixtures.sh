#!/bin/bash
# Remove Test Fixtures

BASE_PATH="/mnt/sdcard/security_camera/security_footage"
TEST_CAMERA="camera_1"

echo "=== Removing Test Fixtures ==="
echo ""
echo "This will remove: $BASE_PATH/$TEST_CAMERA/"
echo ""
read -p "Are you sure? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Removing test fixtures..."
    sudo rm -rf "$BASE_PATH/$TEST_CAMERA"
    echo "✓ Test fixtures removed"
else
    echo "Cancelled"
fi