#!/usr/bin/env python3
import time
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO  # only needed if get_model uses it internally

# 🔧 Adjust this import to match your actual module/file name
# e.g. from targets.nvidia.test import get_model, DEVICE, IMG_SIZE
import util

# Camera settings
CAM_INDEX = 0           # /dev/video0
WIDTH, HEIGHT = 1280, 720
CONF_THRES = 0.25       # YOLO confidence threshold


# Paths
FILE_PATH  = Path(__file__).resolve().parent
MODEL_PATH = (FILE_PATH / "yolo11n.pt").resolve()


def main():
    print(f"[main] Using MODEL_PATH = {MODEL_PATH}")
    # Load model using your utility:
    # - On Jetson (aarch64): creates/loads .engine
    # - On x86: loads .pt directly
    model = util.get_model(MODEL_PATH)

    # Open camera
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {CAM_INDEX}")

    # Set resolution (best effort)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Ask for MJPEG if supported
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    cv2.namedWindow("YOLO11 Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO11 Camera", WIDTH, HEIGHT)

    print("[main] Press 'q' to quit.")

    fps_ema = 0.0
    alpha = 0.1  # smoothing factor; smaller = smoother

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[main] Failed to grab frame")
                break

            t0 = time.time()
            # Serial inference on the raw frame
            results = model(
                frame,
                device=util.DEVICE,
                imgsz=util.IMG_SIZE,
                conf=CONF_THRES,
                verbose=False,
            )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t1 = time.time()
            dt_ms = (t1 - t0) * 1000.0

            # Draw boxes/labels
            annotated = results[0].plot()

            inst_fps = 1000.0 / dt_ms if dt_ms > 0 else 0.0

            if fps_ema == 0.0:
                fps_ema = inst_fps
            else:
                fps_ema = (1.0 - alpha) * fps_ema + alpha * inst_fps

            annotated = results[0].plot()

            fps_text = f"{fps_ema:5.1f} FPS ({dt_ms:4.1f} ms)"

            cv2.putText(
                annotated,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("YOLO11 Camera", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
