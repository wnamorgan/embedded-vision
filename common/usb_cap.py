import cv2

CAM_INDEX = 0          # /dev/video0
WIDTH, HEIGHT = 1920, 1080  # or 640, 360, etc.

# Open camera
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)

if not cap.isOpened():
    raise RuntimeError("Could not open camera")

# Set resolution (best-effort)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# Ask for MJPEG (your camera supports this)
fourcc = cv2.VideoWriter_fourcc(*"MJPG")
cap.set(cv2.CAP_PROP_FOURCC, fourcc)

cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
cv2.namedWindow("Capture", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera", 1280, 720)
cv2.resizeWindow("Capture", 1280, 720)

last_capture = None

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Live preview
        cv2.imshow("Camera", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):  # Space bar → take picture
            last_capture = frame.copy()
            cv2.imshow("Capture", last_capture)
            print("Captured frame")

            # If you want to save to disk, uncomment:
            # cv2.imwrite("capture.jpg", last_capture)

        elif key == ord('q'):  # q → quit
            break

except KeyboardInterrupt:
    # Allow Ctrl+C to exit
    pass

finally:
    cap.release()
    cv2.destroyAllWindows()