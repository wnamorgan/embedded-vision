# UAV Vision Future Spirals & Real-Time Architecture Roadmap

This document describes **future capability spirals** and a **real-time architecture strategy** for the UAV vision system built around:

- Jetson Orin Nano
- Ultralytics YOLO
- USB / Blackfly / Boson cameras
- Future edge accelerators (MemryX, EdgeTPU, Hailo)
- Kalman-based single-object tracking (SOT)

It is intended as a follow-on to the **C-Grade Pipeline Roadmap** and assumes that the basic USB-camera + YOLO + display loop is already working.

---

## 1. Future Spirals & Upgrade Roadmap

Think of these as **ordered spirals**: each adds capability without breaking the previous layers.

### 1.1 Spiral 1 — Stabilize Core Pipeline

**Goal:** Turn the initial C-grade demo into a reliable, repeatable baseline.

Upgrades:
- Robust camera open/close and error handling
- Clear logging of:
  - Frame rate (FPS)
  - Inference time
  - End-to-end latency
- Small configuration file for:
  - Model path
  - Resolution
  - Device (CPU/GPU)
  - ROI size
- On-screen overlay for FPS and status
- Ability to save:
  - Raw frames
  - Annotated frames
  - Logs with timestamps

Outcome: A “known good” baseline that you can always return to.

---

### 1.2 Spiral 2 — Data & Training Enhancements

**Goal:** Improve detector robustness with minimal engineering effort.

Upgrades:
- Acquire diverse real-world samples:
  - Different backgrounds
  - Different lighting / time of day
  - Different ranges and aspect angles
- Expand labeled set (multi-scale, multi-angle)
- Use augmentations:
  - Brightness / contrast jitter
  - Random crops / rotations
  - **Directional motion blur** for UAV rotation and Boson smear
  - Noise injection
- Fine-tune YOLO with 200–500 images
- Benchmark multiple model sizes (`n`, `s`, `m`) on the Nano

Outcome: A detector that behaves stably enough for moving platforms and realistic scenes.

---

### 1.3 Spiral 3 — ROI Tracking Integration

**Goal:** Increase effective resolution and tracking rate.

Upgrades:
- Extract centroid from YOLO bounding box
- Implement a lightweight Kalman filter for:
  - Position
  - Velocity
  - (Optional) scale
- Define an ROI window that follows the target
- Either:
  - Crop ROI from full frame before inference, **or**
  - Move the camera’s hardware ROI (for Blackfly/Boson) based on predicted target location
- Maintain a fallback mode:
  - If track confidence is low
  - Or target is lost
  - → Drop back to full-frame detection

Outcome:
- 60+ Hz effective tracking
- Lower compute load for inference
- More pixels on target inside the effective ROI

---

### 1.4 Spiral 4 — Small-Object Specialization

**Goal:** Handle very small distant targets (few pixels) more robustly.

Upgrades:
- Extend motion-blur augmentation for:
  - Longer blur lengths
  - Multiple directions
- Add specific small-target augmentations:
  - Downscaling objects
  - High-contrast and low-SNR cases
- Re-cluster anchors / use small-object-friendly training options
- Introduce a simple classical fallback:
  - Local contrast filters
  - Correlation tracker
  - Optical flow-based assist around the YOLO detection
- Evaluate performance as target size shrinks (in pixels)

Outcome: System degrades gracefully as targets get small, instead of failing abruptly.

---

### 1.5 Spiral 5 — Multi-Sensor Fusion (Boson + Blackfly)

**Goal:** Combine thermal and visible imagery for robustness and range.

Upgrades:
- Calibrate Boson ↔ Blackfly alignment:
  - Intrinsic and extrinsic calibration
  - Per-pixel mapping between sensors
- Design simple fusion logic:
  - Thermal for coarse detection / all-weather
  - Visible for precision bounding box / geometry
- Try late fusion first:
  - Fuse detections at the bounding-box / track level
  - Rather than early pixel-level fusion
- Evaluate:
  - Day vs night
  - High rotation vs hover
  - Cluttered vs clean backgrounds

Outcome:
- Better long-range performance
- Better low-light performance
- More robust behavior across real-world conditions

---

### 1.6 Spiral 6 — Edge Device Expansion

**Goal:** Make the system portable across different accelerators.

Upgrades per device:
- **MemryX:**
  - Export ONNX from Ultralytics
  - Compile with MemryX toolchain (MXA)
  - Integrate MemryX runtime in the same processing loop
- **EdgeTPU:**
  - Export to TFLite
  - Compile with EdgeTPU compiler
  - Replace the YOLO call with a TFLite + EdgeTPU invocation
- **Hailo:**
  - Convert model via Hailo Model Zoo / compiler
  - Run using Hailo runtime APIs

Common work:
- Retain a uniform pre/post-processing path
- Compare:
  - FPS
  - Latency
  - Power draw
- Keep Ultralytics as the **single source of truth** for model training / export.

Outcome:
- Same conceptual pipeline, multiple hardware backends.

---

### 1.7 Spiral 7 — Gimbal Integration & Stabilized SOT

**Goal:** Turn image-based tracking into active stabilized pointing.

Upgrades:
- Map image-plane error (centroid vs center) → gimbal commands
- Integrate IMU rotation:
  - Predict how target moves across the image during UAV or gimbal motion
- Extend Kalman filter state to:
  - Include bias/misalignment terms if needed
- Test under:
  - High roll rates
  - Aggressive maneuvers
  - Real-world UAV flight profiles

Outcome:
- Camera remains locked on target
- Tracking survives high dynamics better than vision alone.

---

### 1.8 Spiral 8 — Advanced Perception

**Goal:** Move beyond just bounding boxes.

Upgrades:
- Add segmentation head (YOLO-seg) for:
  - Pixel-level masks where useful
- Explore:
  - Depth-from-motion or structure-from-motion to estimate range
  - Target re-identification (ReID) if multiple similar targets
- Implement multi-target tracking:
  - SORT / DeepSORT / ByteTrack
  - Replace or augment the simple SOT approach for more complex scenes

Outcome:
- Richer scene understanding
- Ability to handle multi-target scenarios when needed.

---

### 1.9 Spiral 9 — Synthetic Data Pipeline

**Goal:** Scale dataset size and variety without relying solely on field data.

Upgrades:
- Capture detailed photos of target objects from many angles
- Build 3D mesh (e.g., Meshroom)
- Use BlenderProc (or similar) to:
  - Randomize lighting, backgrounds, materials
  - Vary pose, distance, motion blur
- Mix synthetic and real data:
  - Start with small synthetic fraction
  - Gradually increase as quality improves
- Ensure that Boson / thermal domain is addressed separately:
  - Either via real thermal scenes
  - Or domain-randomized pseudo-thermal rendering (long-term effort)

Outcome:
- Training is no longer limited by collection time
- Easier to cover edge cases (rare angles, lighting, etc.).

---

### 1.10 Spiral 10 — Productionization

**Goal:** Turn the experimental system into a deployable module.

Upgrades:
- Standardize on configuration & logging formats
- Implement health checks and watchdogs:
  - Camera timeouts
  - Model inference failures
- Add telemetry:
  - Latency, FPS, CPU/GPU usage
  - Track quality metrics
- Provide a minimal control UI:
  - Start/Stop
  - Model and resolution selection
  - Device selection (CPU/GPU/accelerator)
- Define clear startup/shutdown sequences

Outcome:
- A robust field-deployable perception component that can run for long periods.

---

## 2. Real-Time Architecture Strategy

This section addresses **how to structure processes/containers** for the pipeline components:

- Camera acquisition (Aravis / USB / other)
- Inference (Ultralytics YOLO)
- Kalman filter & tracking logic
- Optional future fusion and logging

### 2.1 Guiding Principles

1. **C-grade first, then isolate.**  
   Start with the simplest setup that works and is debuggable.

2. **Prefer process boundaries over container boundaries at first.**  
   Use threads and processes inside a single container before splitting into multiple containers.

3. **Only split containers when you have a clear need:**
   - Different dependencies / drivers
   - Different deployment targets (e.g., one module offboard)
   - Clear uptime / restart requirements that benefit from isolation

4. **Keep latency-critical paths short.**  
   Capture → latest frame → inference → tracking should have minimal hops.

---

### 2.2 Single-Container Baseline (Recommended First Architecture)

For the near term, use **one Docker container** that includes:

- Ultralytics + PyTorch + CUDA
- Aravis (when you move beyond USB)
- Your Python application code

Inside that container, split components as:

- **Camera process / thread:**
  - USB or Aravis-based
  - Writes latest frame to a shared buffer (or shared memory)
- **Inference process / thread:**
  - Reads latest frame
  - Runs YOLO
  - Emits bounding box + confidence
- **Tracking (Kalman) process / thread:**
  - Reads detections (centroids, box sizes, confidence)
  - Updates track state
  - Publishes predicted ROI / gimbal command
- **Optional logger/visualizer process:**
  - Receives state, draws overlays, logs metrics

Communication mechanisms inside the container:

- `multiprocessing.Queue` or `Pipe` for low-rate messages (detections, states)
- Shared memory or a single shared image buffer (if/when performance demands it)

This keeps everything:

- Inspectable
- Debbugable
- Easy to profile
- Easy to restart as a single unit

---

### 2.3 Aravis: Same Container or Separate?

**Recommendation for now:**

- Keep **Aravis in the same container** as inference and tracking.

Reasons:

- Shared dependencies are manageable.
- Lower latency (no extra serialization).
- Easier to coordinate camera configuration with ROI logic.

Only consider a **separate Aravis container** if:

- You need it to act as a generic “camera service” used by multiple different clients.
- You want it to run even when the vision/inference container is down.
- You want a very clear separation of responsibilities for different teams.

Even in that case, start with one container and refactor later.

---

### 2.4 Kalman Filter Placement

The Kalman filter is:

- Lightweight
- Pure math
- No external I/O

**Best placement:**

- Either:
  - In the **same process** as inference post-processing (after YOLO, before display), or
  - In a small **separate process** inside the same container if you want stronger separation and clearer testing.

You do **not** need a separate container just for the filter.

Use simple message passing:

- Detection → Kalman → predicted ROI / state
- ROI outputs can be consumed by:
  - Capture process (to move hardware ROI)
  - Inference process (to crop input images)
  - Gimbal control (later spiral)

---

### 2.5 When to Move to Multi-Container / Message Bus

Introduce multiple containers and a message bus (e.g., ZeroMQ, NNG, or gRPC) **later**, when you have clear, concrete motivations such as:

- Offloading inference to a different GPU node
- Splitting camera acquisition from processing across machines
- Hard uptime guarantees (restart one component without touching others)
- Complex deployments (multiple UAVs, ground stations, etc.)

At that stage a typical pattern would be:

- **Container A:** Camera + encoding → publishes frames or compressed ROIs
- **Container B:** Inference + tracking → publishes detections/tracks
- **Container C:** Gimbal control / fusion → consumes track messages

Using:
- ZeroMQ / NNG / gRPC / ROS2 topics as transport

For now, this is **future architecture**, not the immediate target.

---

### 2.6 Summary of Real-Time Architecture Recommendations

1. **Start with one container** for everything (camera, inference, tracking, display).
2. Use **threads or processes** to split:
   - Capture
   - Inference
   - Tracking
3. Use **shared latest frame** + queues for messaging.
4. Keep Aravis **in the same container** until there is a strong reason to split it.
5. Keep the Kalman filter **co-located** with inference or in a small sibling process, not a separate container.
6. Only introduce **multi-container + message bus** when:
   - The single-container system is stable
   - You clearly need distributed deployment or strong isolation.

This staged approach matches your “C-grade first, then refine” philosophy and avoids premature complexity while still leaving a clear path to a more distributed, real-time architecture later.

---

End of document.