#!/bin/bash
# Create Test Fixtures for Helper Functions (Simple Version)
# Creates minimal test files without requiring ImageMagick

echo "=== Creating Test Fixtures (Simple Version) ==="
echo ""

# Base path from config.php
BASE_PATH="/mnt/sdcard/security_camera/security_footage"
TEST_CAMERA="camera_1"
TEST_EVENT_ID="42"
TEST_TIMESTAMP="20251026_143022"

# Create directory structure
echo "Creating directory structure..."
sudo mkdir -p "$BASE_PATH/$TEST_CAMERA/pictures"
sudo mkdir -p "$BASE_PATH/$TEST_CAMERA/videos"
sudo mkdir -p "$BASE_PATH/$TEST_CAMERA/thumbs"

# Create dummy files with minimal content
echo "Creating test files..."

# Thumbnail
THUMB_PATH="$BASE_PATH/$TEST_CAMERA/thumbs/${TEST_EVENT_ID}_${TEST_TIMESTAMP}_thumb.jpg"
echo "Test thumbnail image data" | sudo tee "$THUMB_PATH" > /dev/null
echo "  ✓ Created: $THUMB_PATH"

# Picture A
PICTURE_A_PATH="$BASE_PATH/$TEST_CAMERA/pictures/${TEST_EVENT_ID}_${TEST_TIMESTAMP}_a.jpg"
echo "Test picture A image data" | sudo tee "$PICTURE_A_PATH" > /dev/null
echo "  ✓ Created: $PICTURE_A_PATH"

# Picture B
PICTURE_B_PATH="$BASE_PATH/$TEST_CAMERA/pictures/${TEST_EVENT_ID}_${TEST_TIMESTAMP}_b.jpg"
echo "Test picture B image data" | sudo tee "$PICTURE_B_PATH" > /dev/null
echo "  ✓ Created: $PICTURE_B_PATH"

# H.264 video
H264_PATH="$BASE_PATH/$TEST_CAMERA/videos/${TEST_EVENT_ID}_${TEST_TIMESTAMP}_video.h264"
echo "Test H.264 video data" | sudo tee "$H264_PATH" > /dev/null
echo "  ✓ Created: $H264_PATH"

# MP4 video
MP4_PATH="$BASE_PATH/$TEST_CAMERA/videos/${TEST_EVENT_ID}_${TEST_TIMESTAMP}_video.mp4"
echo "Test MP4 video data" | sudo tee "$MP4_PATH" > /dev/null
echo "  ✓ Created: $MP4_PATH"

# .pending marker for testing video processing
PENDING_PATH="$H264_PATH.pending"
echo "PROCESSING" | sudo tee "$PENDING_PATH" > /dev/null
echo "  ✓ Created: $PENDING_PATH"

# Set permissions
echo ""
echo "Setting permissions..."
sudo chown -R www-data:www-data "$BASE_PATH/$TEST_CAMERA"
sudo chmod -R 755 "$BASE_PATH/$TEST_CAMERA"

echo ""
echo "=== Test Fixtures Created Successfully ==="
echo ""
echo "File structure:"
echo "$BASE_PATH/$TEST_CAMERA/"
echo "├── pictures/"
echo "│   ├── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_a.jpg"
echo "│   └── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_b.jpg"
echo "├── thumbs/"
echo "│   └── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_thumb.jpg"
echo "└── videos/"
echo "    ├── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_video.h264"
echo "    ├── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_video.h264.pending"
echo "    └── ${TEST_EVENT_ID}_${TEST_TIMESTAMP}_video.mp4"
echo ""
echo "Run tests with: cd ~/Security-Camera-Central/www && php test_functions.php"
echo ""
echo "To clean up: sudo rm -rf $BASE_PATH/$TEST_CAMERA"