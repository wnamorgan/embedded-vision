# import cv2

# CAM_INDEX = 2          # /dev/video0
# WIDTH, HEIGHT = 1920, 1080  # or 640, 360, etc.

# # Open camera
# cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)

# if not cap.isOpened():
#     raise RuntimeError("Could not open camera")

# # Set resolution (best-effort)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# # Ask for MJPEG (your camera supports this)
# fourcc = cv2.VideoWriter_fourcc(*"MJPG")
# cap.set(cv2.CAP_PROP_FOURCC, fourcc)

# cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
# cv2.namedWindow("Capture", cv2.WINDOW_NORMAL)
# cv2.resizeWindow("Camera", 1280, 720)
# cv2.resizeWindow("Capture", 1280, 720)

# last_capture = None

# try:
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("Failed to grab frame")
#             break

#         # Live preview
#         cv2.imshow("Camera", frame)

#         key = cv2.waitKey(1) & 0xFF

#         if key == ord(' '):  # Space bar → take picture
#             last_capture = frame.copy()
#             cv2.imshow("Capture", last_capture)
#             print("Captured frame")

#             # If you want to save to disk, uncomment:
#             # cv2.imwrite("capture.jpg", last_capture)

#         elif key == ord('q'):  # q → quit
#             break

# except KeyboardInterrupt:
#     # Allow Ctrl+C to exit
#     pass

# finally:
#     cap.release()
#     cv2.destroyAllWindows()


import cv2
import os
import time
import argparse
from datetime import datetime

WIDTH, HEIGHT = 1920, 1080  # or 640, 360, etc.


def parse_args():
    parser = argparse.ArgumentParser(description="Simple camera capture tool")
    parser.add_argument(
        "-d", "--device",
        type=int,
        default=2,
        help="Camera index (e.g. 0 for /dev/video0, 2 for /dev/video2)"
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

    # Open camera
    cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.device}")

    # Set resolution (best-effort)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Ask for MJPEG (your camera supports this)
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera", 1280, 720)

    # We'll create/destroy "Capture" as needed
    capture_window_visible = False
    capture_shown_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Live preview
            cv2.imshow("Camera", frame)

            # Hide capture window after 1 second if visible
            now = time.time()
            if capture_window_visible and (now - capture_shown_time) > 1.0:
                cv2.destroyWindow("Capture")
                capture_window_visible = False

            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):  # Space bar → take picture
                last_capture = frame.copy()

                # Timestamp filename
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(data_dir, f"{ts}.jpg")
                cv2.imwrite(filename, last_capture)
                print(f"Captured frame -> {filename}")

                # Show capture window
                cv2.imshow("Capture", last_capture)
                cv2.resizeWindow("Capture", 1280, 720)
                capture_window_visible = True
                capture_shown_time = now

            elif key == ord('q'):  # q → quit
                break

    except KeyboardInterrupt:
        # Allow Ctrl+C to exit
        pass

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
