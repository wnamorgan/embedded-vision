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
    unzip \
    && rm -rf /var/lib/apt/lists/*

# (Optional) Install any extra Python packages you know you'll want everywhere
# RUN pip install --no-cache-dir <extra-packages>
# Copy Python deps list
COPY requirements.txt /tmp/requirements.txt
# Install Python deps
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Default workspace inside the container
WORKDIR /workspace/

# Replace headless OpenCV with GUI OpenCV
RUN arch=$(dpkg --print-architecture) && \
    if [ "$arch" = "amd64" ]; then \
        echo "amd64: using pip opencv with GUI backend" && \
        pip uninstall -y opencv-python-headless || true && \
        pip install --no-cache-dir opencv-python; \
    elif [ "$arch" = "arm64" ] || [ "$arch" = "aarch64" ]; then \
        echo "arm64: using system python3-opencv with GTK" && \
        apt-get update && \
        DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
            python3-opencv \
            libgtk-3-0 \
            libglib2.0-0 \
            tzdata \
        && rm -rf /var/lib/apt/lists/* && \
        pip uninstall -y opencv-python-headless opencv-python || true; \
    else \
        echo "Architecture is $arch, leaving OpenCV as-is"; \
    fi

# Don't set an ENTRYPOINT: keep it simple and interactive for now
CMD ["/bin/bash"]
