#!/usr/bin/env bash
set -e

ARCH=$(uname -m)

if [[ "$ARCH" == "x86_64" ]]; then
    BASE_IMAGE="ultralytics/ultralytics:latest"
else
    # assume Jetson / ARM
    BASE_IMAGE="ultralytics/ultralytics:latest-jetson-jetpack6"
fi

echo "Building for $ARCH using base image: $BASE_IMAGE"

IMAGE_NAME="edge_vision:nvidia"

echo "Building image: ${IMAGE_NAME}"
#sudo docker build -t "${IMAGE_NAME}" -f Dockerfile .
docker build \
  --build-arg BASE_IMAGE="$BASE_IMAGE" \
  -t "${IMAGE_NAME}" \
  -f Dockerfile .
echo "Done."
