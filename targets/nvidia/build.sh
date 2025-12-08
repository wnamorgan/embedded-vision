#!/usr/bin/env bash
set -e

IMAGE_NAME="edge_vision:jetson"

echo "Building image: ${IMAGE_NAME}"
sudo docker build -t "${IMAGE_NAME}" -f Dockerfile .
echo "Done."
