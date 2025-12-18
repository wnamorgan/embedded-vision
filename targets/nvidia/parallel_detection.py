#!/usr/bin/env python3
import time
from pathlib import Path
import threading

import cv2
import torch
from ultralytics import YOLO  # only needed if util.get_model uses it internally

import util  # uses util.get_model, util.DEVICE, util.IMG_SIZE

# Camera settings
CAM_INDEX = 0           # /dev/video0
WIDTH, HEIGHT = 1280, 720
CONF_THRES = 0.75       # YOLO confidence threshold

# Paths
FILE_PATH  = Path(__file__).resolve().parent
#MODEL_PATH = (FILE_PATH / "yolo11n_coins.pt").resolve()
MODEL_PATH = (FILE_PATH.parent.parent / "models" / "yolo11n_toy_cars_190.pt").resolve()

def main():
    print(f"[main] Using MODEL_PATH = {MODEL_PATH}")
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

    # Shared state for threads
    latest_frame = {"img": None}
    cond = threading.Condition()
    stop_event = threading.Event()

    def capture_loop():
        """Continuously grab frames from the camera and notify waiters."""
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                # If capture fails, short notify + exit
                with cond:
                    latest_frame["img"] = None
                    cond.notify_all()
                break

            with cond:
                latest_frame["img"] = frame
                cond.notify_all()  # wake up main thread waiting for a frame

    # Start capture thread
    cap_thread = threading.Thread(target=capture_loop, daemon=True)
    cap_thread.start()


    fps_ema = 0.0
    alpha = 0.1  # smoothing factor; smaller = smoother


    try:
        while True:
            # Wait for a frame to be available
            with cond:
                while latest_frame["img"] is None and not stop_event.is_set():
                    cond.wait()

                if stop_event.is_set():
                    break

                frame = latest_frame["img"].copy()

            t0 = time.time()
            results = model(
                frame,
                device=util.DEVICE,
                imgsz=util.IMG_SIZE,
                conf=0.5,
                verbose=False,
            )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t1 = time.time()
            dt_ms = (t1 - t0) * 1000.0

            inst_fps = 1000.0 / dt_ms if dt_ms > 0 else 0.0

            if fps_ema == 0.0:
                fps_ema = inst_fps
            else:
                fps_ema = (1.0 - alpha) * fps_ema + alpha * inst_fps

            r = results[0]
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                annotated = frame.copy()
            else:
                keep = boxes.conf >= CONF_THRES
                boxes = boxes[keep]

            r_filtered = r
            r_filtered.boxes = boxes
            annotated = r_filtered.plot()

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
        stop_event.set()
        with cond:
            cond.notify_all()
        cap_thread.join(timeout=1.0)
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
