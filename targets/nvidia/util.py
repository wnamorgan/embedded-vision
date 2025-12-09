import platform
import time
from pathlib import Path
from ultralytics import YOLO

IMG_SIZE    = 640
DEVICE      = 0

def create_engine(model_path, engine_path, device: int = 0, imgsz: int = 640):
    """
    Export a YOLO model to TensorRT engine if it does not already exist.
    """
    model_path = Path(model_path).resolve()
    engine_path = Path(engine_path).resolve()

    if engine_path.exists():
        print(f"[create_engine] Engine '{engine_path}' already exists, skipping export.")
        return

    print(f"[create_engine] Engine '{engine_path}' not found. Exporting TensorRT engine...")
    model = YOLO(str(model_path))

    model.export(
        format="engine",
        device=device,
        half=True,
        imgsz=imgsz,
    )

    print(f"[create_engine] Export complete (expected file: {engine_path}).")


def get_model(model_path):
    """
    On Jetson (aarch64): ensure TensorRT engine exists and load it.
    On x86: load the PyTorch .pt model directly.
    """
    model_path = Path(model_path).resolve()
    engine_path = model_path.with_suffix(".engine")

    is_jetson = (platform.machine() == "aarch64")

    if is_jetson:
        # Create engine if needed
        create_engine(model_path, engine_path, device=DEVICE, imgsz=IMG_SIZE)

        if not engine_path.exists():
            raise FileNotFoundError(f"[get_model] Engine file '{engine_path}' not found.")

        print(f"[get_model] Loading TensorRT engine from '{engine_path}'...")
        model = YOLO(str(engine_path))
    else:
        print(f"[get_model] Loading PyTorch model from '{model_path}'...")
        model = YOLO(str(model_path))

    return model


# def disp_stats(metrics: dict[str, list[float]], label: str = "[run_model]"):
#     """
#     metrics: dict of {column_name: list_of_values}
#              e.g. {"total_ms": times_ms, "inf_ms": inf_times_ms}
#     """
#     if not metrics:
#         print("disp_stats: no data.")
#         return

#     # Assume all lists same length
#     first_key = next(iter(metrics))
#     n = len(metrics[first_key])
#     if n == 0:
#         print("disp_stats: empty lists.")
#         return

#     # Sort each column once
#     sorted_metrics = {k: sorted(v) for k, v in metrics.items()}

#     def pct(arr, p):
#         idx = int(round((p / 100.0) * (n - 1)))
#         return arr[idx]

#     # --- Summary stats ---
#     print(f"\n{label} Stats over {n} runs")

#     # Header
#     col_names = list(metrics.keys())
#     col_width = 10
#     header = " " * 10 + "".join(f"{name:>{col_width}}" for name in col_names)
#     print(header)

#     # Rows: min, max, mean
#     rows = {
#         "min":  {k: v[0]           for k, v in sorted_metrics.items()},
#         "max":  {k: v[-1]          for k, v in sorted_metrics.items()},
#         "mean": {k: sum(v) / n     for k, v in sorted_metrics.items()},
#     }

#     for row_name, vals in rows.items():
#         line = f"{row_name:>10}:"
#         for k in col_names:
#             line += f"{vals[k]:{col_width}.2f}"
#         print(line)

#     # --- Percentiles ---
#     percentiles = [10, 25, 50, 75, 90, 95, 99, 100]
#     print(f"\n{label} Empirical CDF")
#     header = " " * 10 + "".join(f"{name:>{col_width}}" for name in col_names)
#     print("  pct" + header[3:])  # align roughly with above

#     for p in percentiles:
#         line = f"{p:3d}th :"
#         for k in col_names:
#             val = pct(sorted_metrics[k], p)
#             line += f"{val:{col_width}.2f}"
#         print(line)
def disp_stats(metrics: dict[str, list[float]], label: str = "[run_model]"):
    """
    metrics: dict of {column_name: list_of_values}
             e.g. {"total_ms": times_ms, "inf_ms": inf_times_ms}
    """
    if not metrics:
        print("disp_stats: no data.")
        return

    # Assume all lists same length
    first_key = next(iter(metrics))
    n = len(metrics[first_key])
    if n == 0:
        print("disp_stats: empty lists.")
        return

    # Sort each column once
    sorted_metrics = {k: sorted(v) for k, v in metrics.items()}

    def pct(arr, p):
        idx = int(round((p / 100.0) * (n - 1)))
        return arr[idx]

    # --- Summary stats ---
    print(f"\n{label} Stats over {n} runs")

    col_names = list(metrics.keys())

    # Width for data columns: based on longest header, with padding
    col_width = max(len(name) for name in col_names) + 2
    # Width for the left label column ("min", "max", "mean", "100th", etc.)
    label_width = max(len("100th"), len("mean"), len("pct")) + 2

    # Header
    header = " " * label_width + "".join(f"{name:>{col_width}}" for name in col_names)
    print(header)

    # Rows: min, max, mean
    rows = {
        "min":  {k: v[0]       for k, v in sorted_metrics.items()},
        "max":  {k: v[-1]      for k, v in sorted_metrics.items()},
        "mean": {k: sum(v) / n for k, v in sorted_metrics.items()},
    }

    for row_name, vals in rows.items():
        line = f"{row_name:>{label_width}}:"
        for k in col_names:
            line += f"{vals[k]:{col_width}.2f}"
        print(line)

    # --- Percentiles ---
    percentiles = [10, 25, 50, 75, 90, 95, 99, 100]
    print(f"\n{label} Empirical CDF")

    # Reuse same header alignment
    print(f"{'pct':>{label_width}} " + "".join(f"{name:>{col_width}}" for name in col_names))

    for p in percentiles:
        label_str = f"{p}th"
        line = f"{label_str:>{label_width}}:"
        for k in col_names:
            val = pct(sorted_metrics[k], p)
            line += f"{val:{col_width}.2f}"
        print(line)
