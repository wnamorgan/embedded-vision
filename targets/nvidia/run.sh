#!/usr/bin/env bash
set -e

IMAGE="edge_vision:jetson"

# Directory where this script lives (same as Dockerfile)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Go two levels up from SCRIPT_DIR (adjust the number of .. if your layout changes)
WORKSPACE_HOST_DIR="$( realpath "${SCRIPT_DIR}/../.." )"

echo "Script dir:           ${SCRIPT_DIR}"
echo "Host workspace dir:   ${WORKSPACE_HOST_DIR}"

# Allow X from containers
xhost +local:root

sudo docker run -it --rm \
  --runtime=nvidia \
  --gpus all \
  --ipc=host \
  --network=host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --device /dev/video0:/dev/video0 \
  -v /dev/bus/usb:/dev/bus/usb \
  -v "${WORKSPACE_HOST_DIR}:/workspace" \
  "${IMAGE}" \
  bash
