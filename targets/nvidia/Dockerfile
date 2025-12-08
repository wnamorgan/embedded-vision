# Base: Ultralytics Jetson image with JetPack 6, CUDA, PyTorch, TensorRT, Ultralytics
FROM ultralytics/ultralytics:latest-jetson-jetpack6

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

# Default workspace inside the container
WORKDIR /workspace/

# Don't set an ENTRYPOINT: keep it simple and interactive for now
CMD ["/bin/bash"]
