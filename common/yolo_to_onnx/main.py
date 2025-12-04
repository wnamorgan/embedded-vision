from ultralytics import YOLO
import os, sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "xcb"

ROOT = Path(__file__).resolve().parents[1]   
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opencv_inference.util import img_inference


def test_exported_model():
    zidane_path = ROOT / "opencv_inference" / "zidane.jpg"
    onnx_path = ROOT / "yolov8n.onnx"

    img_inference(str(onnx_path), str(zidane_path))


def load_and_export_model():
    # NOTE: point YOLO at the weights in ROOT explicitly
    model = YOLO(str(ROOT / "yolov8n.pt"))
    model.export(format="onnx", opset=12, dynamic=False)


def main():
    load_and_export_model()
    test_exported_model()


if __name__ == "__main__":
    main()
