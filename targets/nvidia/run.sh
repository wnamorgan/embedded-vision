#!/usr/bin/env bash
set -e

IMAGE="edge_vision:nvidia"

# Directory where this script lives (same as Dockerfile)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Go two levels up from SCRIPT_DIR (adjust the number of .. if your layout changes)
WORKSPACE_HOST_DIR="$( realpath "${SCRIPT_DIR}/../.." )"

echo "Script dir:           ${SCRIPT_DIR}"
echo "Host workspace dir:   ${WORKSPACE_HOST_DIR}"

# Allow X from containers
xhost +local:root

# Decide GPU flags (same idea as before, optional)
GPU_FLAGS=""
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_FLAGS="--gpus all"
    if docker info 2>/dev/null | grep -q ' Runtimes:.*nvidia'; then
        GPU_FLAGS="$GPU_FLAGS --runtime=nvidia"
    fi
else
    echo "Warning: nvidia-smi not found; running container without GPU access."
fi

# Optional device flags
DEVICE_FLAGS=""
if [[ -e /dev/video0 ]]; then
    DEVICE_FLAGS+=" --device /dev/video0:/dev/video0"
else
    echo "Note: /dev/video0 not found; starting container without camera device."
fi

if [[ -d /dev/bus/usb ]]; then
    DEVICE_FLAGS+=" -v /dev/bus/usb:/dev/bus/usb"
else
    echo "Note: /dev/bus/usb not found; USB bus not mounted into container."
fi

docker run -it --rm \
  ${GPU_FLAGS} \
  --ipc=host \
  --network=host \
  --privileged \
  -e DISPLAY="$DISPLAY" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  ${DEVICE_FLAGS} \
  -v "${WORKSPACE_HOST_DIR}:/workspace" \
  -v /dev:/dev \
  "${IMAGE}" \
  bash
