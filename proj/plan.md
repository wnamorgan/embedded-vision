# UAV Vision Pipeline Roadmap — C-Grade First Pass

## 1. Purpose
Build a minimal, reliable **C-grade end-to-end perception loop** on the Jetson Orin Nano to establish the foundation for all future work (dataset creation, training, edge accelerators, Boson integration, ROI tracking, Kalman filter, etc.).

This document captures:
- Key decisions made  
- Architecture chosen  
- Immediate next steps  
- Deferred tasks (to avoid rabbit holes)  

---

## 2. Current Architecture Decisions

### 2.1 Inference Framework
**Ultralytics YOLO (YOLOv8/YOLOv11)** chosen as the single unified framework across:
- Jetson Orin Nano  
- MemryX  
- Edge TPU  
- Hailo  

Avoids:
- TensorRT low-level glue  
- jetson-inference (Dusty’s) Jetson-only ecosystem  

Export paths preserved (ONNX, TensorRT engine, TFLite, etc.)  
**Status: Locked in.**

---

### 2.2 Deployment Strategy
Use **Ultralytics Jetson Docker container** for:
- Correct CUDA/PyTorch build  
- Consistent environment  
- Easier future edge portability  

Run the camera + inference loop **inside the container** using host X11 for display.  
**Status: Locked in.**

---

### 2.3 Camera Acquisition Model (First Demo)
Use **USB UVC camera** first (zero friction).

Two-thread design:
- **Thread 1 → Capture** (overwrite `latest_frame`, no queue buildup)
- **Thread 2 → Process** (YOLO inference + annotation + display)

This ensures:
- Zero latency backlog  
- Smooth real-time behavior  
- Clean place to later add ROI cropping  

**Status: Locked in.**

---

### 2.4 Processing Pipeline
1. Capture frame  
2. Grab **latest frame only**  
3. Run YOLO model on GPU  
4. Annotate frame (`results[0].plot()`)  
5. Display using `cv2.imshow()`  
6. Optional: save raw frames for dataset creation (`'s'` key)

The simplest pipeline that still provides:
- GPU inference  
- Real-time visualization  
- Ability to capture training data  

**Status: Locked in.**

---

## 3. What We Are Explicitly *Not* Doing Now
To protect schedule and avoid rabbit holes, the following are deferred:

- ❌ TensorRT manual bindings  
- ❌ jetson-inference (Dusty)  
- ❌ Boson thermal pipeline  
- ❌ Synthetic data via Blender/BlenderProc  
- ❌ Network modifications (small-object heads, attention blocks, custom necks)  
- ❌ ROI tracking  
- ❌ Kalman SOT integration  
- ❌ Multi-accelerator performance optimization  
- ❌ General CV tuning (histogram equalization, etc.)

**Reason:** These all build on a stable C-grade pipeline.

---

## 4. Immediate Short-Term Plan (1–2 Days)

### 4.1 Step 1 — Run Single-Image YOLO on GPU
Inside the container:

```python
from ultralytics import YOLO
import cv2, time

model = YOLO("yolo11n.pt").to("cuda:0")
img = cv2.imread("test.jpg")

t0 = time.time()
results = model(img, device=0, imgsz=640)
t1 = time.time()

print("Inference time:", (t1 - t0)*1000, "ms")
```

**Goal:** Confirm CUDA is active and GPU inference works.

---

### 4.2 Step 2 — Implement Two-Thread Live USB Camera Demo
- Thread 1: capture → update `latest_frame`  
- Thread 2: YOLO on latest → annotate → display  

Controls:
- Press **`s`** to save images for labeling  
- Press **`q`** to exit  

**Goal:** Show live annotated camera feed from YOLO on GPU.  
**This is the C-grade success milestone.**

---

### 4.3 Step 3 — Begin Dataset Collection
During demo:
- Press `'s'` to save raw frames  
- Collect ~20–50 images  
- Move them to labeling tool (Label Studio, CVAT, Roboflow)

**Goal:** Build the seed of a real dataset.

---

## 5. Medium-Term Next Steps (After C-Grade Demo)
Choose **one path** next:

---

### **Path A — Train Your Own YOLO Model (Recommended Next)**
- Label the 20–50 images  
- Train in Colab or localhost  
- Export (`yolo export`)  
- Run inference on Nano with your custom model  

Provides **immediate accuracy improvement**.

---

### **Path B — Bring Up a Second Edge Device**
E.g., **MemryX M.2**:
- Use same Ultralytics pipeline  
- Compare speed + accuracy  
- Validate cross-platform portability  

---

### **Path C — Integrate ROI + Kalman SOT**
- Add bounding-box → centroid extraction  
- Add Kalman filter (adaptive R based on confidence + box size)  
- Use predicted ROI for next frame capture  
- Later replace USB cam with Blackfly/Boson  

---

### **Path D — Synthetic Data (BlenderProc)**
When ready for high-variation datasets:
- Build crude 3D mesh  
- Randomize textures, lighting, angle  
- Render thousands of synthetic training samples  
- Combine with real captures  

Large payoff, but only **after pipeline is stable**.

---

## 6. Long-Term Architecture Vision
### **Thermal + Visible camera fusion**
- Boson for heat signature  
- Blackfly for long-range precision  

### **ROI-based high-rate tracking**
- Crop around predicted target  
- Dramatically increases effective resolution  
- Enables 60+ Hz SOT  

### **Edge-accelerated inference**
Same Ultralytics model across:
- Nano (TensorRT)  
- MemryX (MXA compiler)  
- Hailo (HEF)  
- EdgeTPU (TFLite)

### **Robust small-target handling**
- Fallback to non-YOLO classical motion filters if needed  
- Kalman smoothing  
- Track-before-detect for very small pixels  

---

## 7. You Are Here → What to Do Next
### **TODAY’S PRIORITY**
- ✔ Bring up Ultralytics Docker  
- ✔ Confirm GPU inference  
- ✔ Run two-thread camera → YOLO → display loop  
- ✔ Save several frames  

### **TOMORROW**
- ✔ Label dataset  
- ✔ Start small YOLO fine-tune  
- ✔ Re-test on Nano  

Everything beyond this builds cleanly on that foundation.

---

## 8. Final Notes
- You have not moved slowly; you’ve been defining architecture correctly.  
- You avoided multiple deep rabbit holes.  
- The path ahead is now linear and stable.  
- The C-grade demo is well within reach.  

Once you complete Step 1 + Step 2, you’ll have a functioning UAV vision pipeline you can extend indefinitely.