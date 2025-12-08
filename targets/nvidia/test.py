#!/usr/bin/env python3
import os
import time

import cv2
import torch
from ultralytics import YOLO

FILE_PATH   = os.path.dirname(os.path.abspath(__file__))
from pathlib import Path

FILE_PATH   = Path(__file__).resolve().parent
IMG_PATH    = (FILE_PATH / ".." / ".." / "common" / "opencv_inference" / "zidane.jpg").resolve()
ENGINE_PATH = (FILE_PATH / "yolo11n.engine").resolve()
MODEL_PATH  = (FILE_PATH / "yolo11n.pt").resolve()
DEVICE      = 0                  # Jetson GPU is usually device 0
IMG_SIZE    = 640                # inference size
N_RUNS      = 100                # how many times to time the engine


def create_engine(model_path: str, engine_path: str, device: int = 0, imgsz: int = 640):
    """
    Export a YOLO model to TensorRT engine if it does not already exist.
    """
    if os.path.exists(engine_path):
        print(f"[create_engine] Engine '{engine_path}' already exists, skipping export.")
        return

    print(f"[create_engine] Engine '{engine_path}' not found. Exporting TensorRT engine...")
    model = YOLO(model_path)

    # FP16 TensorRT engine; adjust as needed
    model.export(
        format="engine",
        device=device,
        half=True,
        imgsz=imgsz,
    )

    print(f"[create_engine] Export complete (expected file: {engine_path}).")

import time
import os
import cv2
import torch
from ultralytics import YOLO

def run_engine(engine_path: str, img_path: str, device: int = 0, imgsz: int = 640, n_runs: int = 50):
    """
    Load a TensorRT engine and run repeated inference, reporting a cumulative distribution
    (percentiles) of total per-call times.
    """
    if not os.path.exists(engine_path):
        raise FileNotFoundError(f"[run_engine] Engine file '{engine_path}' not found.")

    print(f"[run_engine] Loading engine from '{engine_path}'...")
    model = YOLO(engine_path)

    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"[run_engine] Could not read image '{img_path}'.")

    # Warmup (don't time this)
    print("[run_engine] Warming up...")
    for _ in range(5):
        _ = model(img, device=device, imgsz=imgsz, verbose=False)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    print(f"[run_engine] Running {n_runs} timed inferences (verbose=False)...")
    times_ms = []
    inf_times_ms = []
    for _ in range(n_runs):
        t0 = time.time()
        results = model(img, device=device, imgsz=imgsz, verbose=False)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t1 = time.time()
        times_ms.append((t1 - t0) * 1000.0)
        inf_ms = results[0].speed["inference"]
        inf_times_ms.append(inf_ms)

    disp_stats(times_ms, inf_times_ms)

def disp_stats(times_ms, inf_times_ms):
    # Basic stats for wall time (times_ms) and inference time (inf_times_ms)
    total_sorted = sorted(times_ms)
    inf_sorted = sorted(inf_times_ms)
    n = len(total_sorted)

    def pct(arr, p):
        idx = int(round((p / 100.0) * (n - 1)))
        return arr[idx]

    mean_total = sum(total_sorted) / n
    mean_inf = sum(inf_sorted) / n

    print(f"\n[run_engine] Stats over {n} runs")
    print("                total_ms   inf_ms")
    print(f"  min   :      {total_sorted[0]:7.2f}  {inf_sorted[0]:7.2f}")
    print(f"  max   :      {total_sorted[-1]:7.2f}  {inf_sorted[-1]:7.2f}")
    print(f"  mean  :      {mean_total:7.2f}  {mean_inf:7.2f}")

    # Empirical CDF via percentiles
    percentiles = [10, 25, 50, 75, 90, 95, 99, 100]
    print("\n[run_engine] Empirical CDF")
    print("  pct        total_ms   inf_ms")
    for p in percentiles:
        t_val = pct(total_sorted, p)
        i_val = pct(inf_sorted, p)
        print(f"  {p:3d}th :    {t_val:7.2f}  {i_val:7.2f}")    


def main():
    create_engine(MODEL_PATH, ENGINE_PATH, device=DEVICE, imgsz=IMG_SIZE)
    run_engine(ENGINE_PATH, IMG_PATH, device=DEVICE, imgsz=IMG_SIZE, n_runs=N_RUNS)


if __name__ == "__main__":
    main()
