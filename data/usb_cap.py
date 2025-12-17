


# import cv2
# import os
# import time
# import argparse
# from datetime import datetime

# WIDTH, HEIGHT = 1920, 1080  # or 640, 360, etc.


# def parse_args():
#     parser = argparse.ArgumentParser(description="Simple camera capture tool")
#     parser.add_argument(
#         "-d", "--device",
#         type=int,
#         default=0,
#         help="Camera index (e.g. 0 for /dev/video0, 2 for /dev/video2)"
#     )
#     return parser.parse_args()


# def make_data_dir(prefix="data"):
#     """
#     Create the first available directory in the form data001..data999
#     and return its path.
#     """
#     for i in range(1, 1000):
#         name = f"{prefix}{i:03d}"
#         if not os.path.exists(name):
#             os.makedirs(name)
#             return name
#     raise RuntimeError("All data001..data999 directories already exist.")


# def main():
#     args = parse_args()
#     data_dir = make_data_dir()
#     print(f"Saving captures to: {data_dir}")
#     print("Press SPACE to capture, 'q' to quit.")

#     # Open camera
#     cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)

#     if not cap.isOpened():
#         raise RuntimeError(f"Could not open camera index {args.device}")

#     # Set resolution (best-effort)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

#     # Ask for MJPEG (your camera supports this)
#     fourcc = cv2.VideoWriter_fourcc(*"MJPG")
#     cap.set(cv2.CAP_PROP_FOURCC, fourcc)

#     cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
#     cv2.resizeWindow("Camera", 1280, 720)

#     # We'll create/destroy "Capture" as needed
#     capture_window_visible = False
#     capture_shown_time = 0.0

#     try:
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 print("Failed to grab frame")
#                 break

#             # Live preview
#             cv2.imshow("Camera", frame)

#             # Hide capture window after 1 second if visible
#             now = time.time()
#             if capture_window_visible and (now - capture_shown_time) > 1.0:
#                 cv2.destroyWindow("Capture")
#                 capture_window_visible = False

#             key = cv2.waitKey(1) & 0xFF

#             if key == ord(' '):  # Space bar → take picture
#                 last_capture = frame.copy()

#                 # Timestamp filename
#                 ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#                 filename = os.path.join(data_dir, f"{ts}.jpg")
#                 cv2.imwrite(filename, last_capture)
#                 print(f"Captured frame -> {filename}")

#                 # Show capture window
#                 cv2.imshow("Capture", last_capture)
#                 cv2.resizeWindow("Capture", 1280, 720)
#                 capture_window_visible = True
#                 capture_shown_time = now

#             elif key == ord('q'):  # q → quit
#                 break

#     except KeyboardInterrupt:
#         # Allow Ctrl+C to exit
#         pass

#     finally:
#         cap.release()
#         cv2.destroyAllWindows()


# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
import cv2
import os
import time
import argparse
from datetime import datetime

WIDTH, HEIGHT = 1920, 1080  # change if you want


def parse_args():
    parser = argparse.ArgumentParser(description="Camera capture tool (optional YOLO overlay)")
    parser.add_argument(
        "-d", "--device",
        type=int,
        default=0,
        help="Camera index (e.g. 0 for /dev/video0, 2 for /dev/video2)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Optional path to a YOLO model (e.g. runs/yolo/weights/best.pt). If omitted, no inference is done."
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for YOLO (only used when -m is set)."
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.7,
        help="IoU threshold for NMS (only used when -m is set)."
    )
    parser.add_argument(
        "--infer-every",
        type=int,
        default=1,
        help="Run inference every N frames (only used when -m is set)."
    )
    return parser.parse_args()


def make_data_dir(prefix="data"):
    """
    Create the first available directory in the form data001..data999
    and return its path.
    """
    for i in range(1, 1000):
        name = f"{prefix}{i:03d}"
        if not os.path.exists(name):
            os.makedirs(name)
            return name
    raise RuntimeError("All data001..data999 directories already exist.")


def main():
    args = parse_args()
    data_dir = make_data_dir()
    print(f"Saving captures to: {data_dir}")
    print("Press SPACE to capture, 'q' to quit.")

    # Optional YOLO model load (lazy import so script can run without ultralytics installed)
    model = None
    if args.model:
        try:
            from ultralytics import YOLO
        except Exception as e:
            raise RuntimeError(
                "You provided -m/--model, but ultralytics is not available in this environment.\n"
                "Activate your ultralytics venv or install it (pip install ultralytics).\n"
                f"Import error: {e}"
            )
        print(f"Loading YOLO model: {args.model}")
        model = YOLO(args.model)

    # Open camera
    cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.device}")

    # Set resolution (best-effort)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Ask for MJPEG (best-effort)
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera", 1280, 720)

    # We'll create/destroy "Capture" as needed
    capture_window_visible = False
    capture_shown_time = 0.0

    # Inference throttling + caching last annotated frame
    frame_idx = 0
    last_vis = None

    # Optional warmup so first inference isn't a big hiccup
    warmed = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            frame_idx += 1
            frame_raw = frame  # always save raw

            # Decide what to display
            frame_vis = frame_raw

            if model is not None:
                do_infer = (frame_idx % max(1, args.infer_every) == 0)

                if do_infer or last_vis is None:
                    # Warmup once
                    if not warmed:
                        try:
                            _ = model.predict(frame_raw, conf=args.conf, iou=args.iou, verbose=False)
                        except Exception:
                            pass
                        warmed = True

                    results = model.predict(
                        frame_raw,
                        conf=args.conf,
                        iou=args.iou,
                        verbose=False
                    )
                    # Ultralytics built-in render (annotated image)
                    frame_vis = results[0].plot()
                    last_vis = frame_vis
                else:
                    # reuse last annotated frame if we're skipping inference this frame
                    frame_vis = last_vis

            # Live preview (annotated if model provided)
            cv2.imshow("Camera", frame_vis)

            # Hide capture window after 1 second if visible
            now = time.time()
            if capture_window_visible and (now - capture_shown_time) > 1.0:
                cv2.destroyWindow("Capture")
                capture_window_visible = False

            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):  # Space bar → save RAW picture
                last_capture = frame_raw.copy()

                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(data_dir, f"{ts}.jpg")
                ok = cv2.imwrite(filename, last_capture)
                if ok:
                    print(f"Captured raw frame -> {filename}")
                else:
                    print(f"WARNING: Failed to write -> {filename}")

                # Show capture window (raw)
                cv2.imshow("Capture", last_capture)
                cv2.resizeWindow("Capture", 1280, 720)
                capture_window_visible = True
                capture_shown_time = now

            elif key == ord('q'):
                break

    except KeyboardInterrupt:
        pass

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
