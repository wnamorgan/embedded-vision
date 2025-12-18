import platform
import time
from pathlib import Path
from ultralytics import YOLO

IMG_SIZE    = 640
DEVICE      = 0
FP16        = True
USE_ENGINE  = True


def create_engine(model_path, engine_path, device: int = 0, imgsz: int = 640):
    """
    Export a YOLO model to TensorRT engine if it does not already exist.
    Deletes the intermediate ONNX file and appends _FP16 or _FP32 to the engine file.
    """
    model_path = Path(model_path).resolve()
    engine_path = Path(engine_path).resolve()

    if engine_path.exists():
        print(f"[create_engine] Engine '{engine_path}' already exists, skipping export.")
        return

    print(f"[create_engine] Engine '{engine_path}' not found. Exporting TensorRT engine...")
    model = YOLO(str(model_path))

    # Export to TensorRT engine
    model.export(
        format="engine",
        device=device,
        half=FP16,  # Use FP16 if flag is True
        imgsz=imgsz,
    )

    # After exporting, get the correct engine name based on FP16 flag
    engine_filename = f"{engine_path.stem}_{'FP16' if FP16 else 'FP32'}{engine_path.suffix}"
    engine_path = engine_path.with_name(engine_filename)

    # Rename the engine file to include _FP16 or _FP32
    model.model.save(engine_path)

    # Delete the intermediate ONNX file if it exists
    onnx_path = model_path.with_suffix(".onnx")
    if onnx_path.exists():
        onnx_path.unlink()  # Delete the ONNX file
        print(f"[create_engine] Deleted intermediate ONNX file: {onnx_path}")

    print(f"[create_engine] Export complete. Engine saved as: {engine_path}")


def describe_model(model):
    # Check if the model is a TensorRT engine or a PyTorch model
    if hasattr(model, 'model') and hasattr(model.model, 'args'):
        # For PyTorch models
        precision = "FP16" if model.model.args.get('half', False) else "FP32"
        print(f"Model type: PyTorch | Precision: {precision}")
    else:
        # For TensorRT engines
        precision = "FP16" if "_FP16" in model.__str__() else "FP32"
        print(f"Model type: TensorRT | Precision: {precision}")

def get_model(model_path):
    """
    On Jetson (aarch64): ensure TensorRT engine exists and load it.
    On x86: load the PyTorch .pt model directly.
    """
    model_path = Path(model_path).resolve()
    
    # Strip any existing precision suffix from the model name (i.e., _FP16 or _FP32)
    model_name = model_path.stem  # Base name without suffix
    engine_path_fp16 = model_path.with_name(f"{model_name}_FP16.engine")
    engine_path_fp32 = model_path.with_name(f"{model_name}_FP32.engine")

    is_jetson = (platform.machine() == "aarch64")

    if is_jetson and USE_ENGINE:
        # Check for the correct engine based on FP16 flag
        if FP16 and engine_path_fp16.exists():
            print(f"[get_model] Loading TensorRT engine (FP16) from '{engine_path_fp16}'...")
            model = YOLO(str(engine_path_fp16))
        elif not FP16 and engine_path_fp32.exists():
            print(f"[get_model] Loading TensorRT engine (FP32) from '{engine_path_fp32}'...")
            model = YOLO(str(engine_path_fp32))
        else:
            # Engine doesn't exist, create one
            print(f"[get_model] Engine not found. Creating TensorRT engine with {'FP16' if FP16 else 'FP32'} precision...")
            create_engine(model_path, engine_path_fp16 if FP16 else engine_path_fp32, device=DEVICE, imgsz=IMG_SIZE)
            model = YOLO(str(engine_path_fp16 if FP16 else engine_path_fp32))

    else:
        print(f"[get_model] Loading PyTorch model from '{model_path}'...")
        model = YOLO(str(model_path))

    # Describe the model after loading
    describe_model(model)

    return model




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
