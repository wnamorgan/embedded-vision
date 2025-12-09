#!/usr/bin/env python3
import os
import time
from pathlib import Path
import platform

import cv2
import torch


import util 

# Paths and constants
FILE_PATH   = Path(__file__).resolve().parent
IMG_PATH    = (FILE_PATH / ".." / ".." / "common" / "opencv_inference" / "zidane.jpg").resolve()
MODEL_PATH  = (FILE_PATH / "yolo11n.pt").resolve()   # define ONLY the .pt here
DEVICE      = 0
IMG_SIZE    = 640
N_RUNS      = 100


def run_model(model, img_path: str, device: int = 0, imgsz: int = 640, n_runs: int = 50):
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"[run_model] Could not read image '{img_path}'.")

    print("[run_model] Warming up...")
    for _ in range(5):
        _ = model(img, device=device, imgsz=imgsz, verbose=False)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    print(f"[run_model] Running {n_runs} timed inferences (verbose=False)...")
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

    metrics = {
        "total_ms": times_ms,
        "inf_ms": inf_times_ms,
    }
    util.disp_stats(metrics)


def main():
    model = util.get_model(MODEL_PATH)
    run_model(model, str(IMG_PATH), device=DEVICE, imgsz=IMG_SIZE, n_runs=N_RUNS)


if __name__ == "__main__":
    main()
