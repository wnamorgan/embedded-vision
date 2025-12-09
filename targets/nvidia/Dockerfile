# syntax=docker/dockerfile:1.4
# Base: Ultralytics Jetson image with JetPack 6, CUDA, PyTorch, TensorRT, Ultralytics
# Default to Jetson image, but allow override
ARG BASE_IMAGE=ultralytics/ultralytics:latest-jetson-jetpack6
FROM ${BASE_IMAGE}

# Optional: label for clarity
LABEL maintainer="wnamorgan@github.com" \
      description="Embedded Vision dev image (Ultralytics + tools)"

# Install some basic tools now (safe, lightweight)
# You can add Aravis or other libs later in this same layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    nano \
    git \
    htop \
    && rm -rf /var/lib/apt/lists/*

# (Optional) Install any extra Python packages you know you'll want everywhere
# RUN pip install --no-cache-dir <extra-packages>
RUN pip install --no-cache-dir "ultralytics[export]"

# Default workspace inside the container
WORKDIR /workspace/

# Only on x86_64 (amd64): replace headless OpenCV with GUI OpenCV
RUN arch=$(dpkg --print-architecture) && \
    if [ "$arch" = "amd64" ]; then \
        pip uninstall -y opencv-python-headless && \
        pip install --no-cache-dir opencv-python; \
    else \
        echo "Architecture is $arch, leaving OpenCV as-is"; \
    fi

# Don't set an ENTRYPOINT: keep it simple and interactive for now
CMD ["/bin/bash"]
