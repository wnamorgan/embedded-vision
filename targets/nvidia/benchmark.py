from ultralytics import YOLO

# Load a YOLO11n PyTorch model
model = YOLO("yolo11n.pt")

# Benchmark YOLO11n speed and accuracy on the COCO128 dataset for all all export formats
results = model.benchmark(data="coco128.yaml", imgsz=640)