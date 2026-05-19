"""
compCV.py  — LEGO Detector (Pink Object + Yellow Minifigure)
─────────────────────────────────────────────────────────────────────────────
Camo Camera Edition
─────────────────────────────────────────────────────────────────────────────
What it does:
    1. Connects to the Camo Camera app (phone as webcam).
    2. Detects a PINK LEGO object  → draws a GREEN box + label.
    3. Detects a YELLOW LEGO character (minifigure) → draws a GREEN box + label.
    4. Calculates & displays the distance (cm) for every detected object.

How to use:
    ① Open Camo on phone + PC, connect via USB or Wi-Fi.
    ② Run:  python compCV.py
    ③ Press  Q  to quit.
    ④ Press  C  to open live color-tuner sliders.

Requirements:
    pip install opencv-python numpy
─────────────────────────────────────────────────────────────────────────────
"""

import cv2
import numpy as np
import sys
import threading



CAMERA_INDEX = 0   # Try 1 or 2 if Camo camera is not on index 0

# ── Known real-world sizes ───────────────────────────────────
LEGO_CHAR_HEIGHT_CM  = 4.0   # LEGO minifigure height  (~4 cm)
LEGO_THING_HEIGHT_CM = 3.2   # LEGO pink object height (adjust to your piece)


CALIB_PX          = None
CALIB_DISTANCE_CM = 20
FOCAL_LENGTH      = 500.0

if CALIB_PX is not None:
    FOCAL_LENGTH = (CALIB_PX * CALIB_DISTANCE_CM) / LEGO_CHAR_HEIGHT_CM
    print(f"[INFO] Focal length (calibrated): {FOCAL_LENGTH:.2f} px")
else:
    print("[INFO] Using default focal length. Hold LEGO 20 cm away and set CALIB_PX.")



# 🟡 YELLOW  — classic LEGO minifigure body/head colour
YELLOW_LOWER = np.array([ 18, 100, 100], dtype=np.uint8)
YELLOW_UPPER = np.array([ 35, 255, 255], dtype=np.uint8)

# 🟪 PINK / PINKY  — the LEGO pink object/thing
PINK_LOWER   = np.array([140,  60,  80], dtype=np.uint8)
PINK_UPPER   = np.array([175, 255, 255], dtype=np.uint8)

# ── Detection filters ────────────────────────────────────────
MIN_AREA     = 600
MAX_AREA     = 90000
MIN_SOLIDITY = 0.35

# ── Visual style ─────────────────────────────────────────────
BOX_COLOR     = (0, 255, 0)    # Green for all boxes
FONT          = cv2.FONT_HERSHEY_SIMPLEX



class CameraStream:
    def __init__(self, index):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self._lock = threading.Lock()
        self._running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self._running:
            ret, frame = self.cap.read()
            with self._lock:
                self.ret, self.frame = ret, frame

    def read(self):
        with self._lock:
            return self.ret, self.frame.copy() if self.ret else (False, None)

    def release(self):
        self._running = False
        self.cap.release()


def estimate_distance(pixel_height: float, known_cm: float) -> float:
    if pixel_height <= 0:
        return 0.0
    return (known_cm * FOCAL_LENGTH) / pixel_height


def find_objects(mask):
    """Return list of bounding rects (x,y,w,h) for valid blobs in mask."""
    kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask     = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
    mask     = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA or area > MAX_AREA:
            continue
        hull      = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity  = area / hull_area if hull_area > 0 else 0
        if solidity < MIN_SOLIDITY:
            continue
        rects.append(cv2.boundingRect(cnt))
    return rects


def draw_box(frame, x, y, w, h, label, dist_cm):
    """Draw green box + distance label on frame."""
    # Green rectangle
    cv2.rectangle(frame, (x, y), (x + w, y + h), BOX_COLOR, 2)

    # Semi-transparent fill
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 100), -1)
    cv2.addWeighted(overlay, 0.12, frame, 0.88, 0, frame)

    # Label text
    text    = f"{label}  {dist_cm:.1f} cm"
    label_y = y - 10 if y - 10 > 15 else y + h + 22
    (lw, lh), _ = cv2.getTextSize(text, FONT, 0.65, 2)

    # Dark background behind text
    cv2.rectangle(frame,
                  (x, label_y - lh - 5),
                  (x + lw + 6, label_y + 5),
                  (0, 0, 0), -1)
    cv2.putText(frame, text,
                (x + 3, label_y),
                FONT, 0.65, BOX_COLOR, 2, cv2.LINE_AA)




TUNER_WIN = "Color Tuner — close to hide"

def create_tuner(lower_y, upper_y, lower_p, upper_p):
    cv2.namedWindow(TUNER_WIN)
    # Yellow sliders
    cv2.createTrackbar("YEL H-Low",  TUNER_WIN, int(lower_y[0]), 180, lambda v: None)
    cv2.createTrackbar("YEL H-High", TUNER_WIN, int(upper_y[0]), 180, lambda v: None)
    cv2.createTrackbar("YEL S-Low",  TUNER_WIN, int(lower_y[1]), 255, lambda v: None)
    cv2.createTrackbar("YEL V-Low",  TUNER_WIN, int(lower_y[2]), 255, lambda v: None)
    # Pink sliders
    cv2.createTrackbar("PNK H-Low",  TUNER_WIN, int(lower_p[0]), 180, lambda v: None)
    cv2.createTrackbar("PNK H-High", TUNER_WIN, int(upper_p[0]), 180, lambda v: None)
    cv2.createTrackbar("PNK S-Low",  TUNER_WIN, int(lower_p[1]), 255, lambda v: None)
    cv2.createTrackbar("PNK V-Low",  TUNER_WIN, int(lower_p[2]), 255, lambda v: None)

def read_tuner(lower_y, upper_y, lower_p, upper_p):
    try:
        y_hl = cv2.getTrackbarPos("YEL H-Low",  TUNER_WIN)
        y_hh = cv2.getTrackbarPos("YEL H-High", TUNER_WIN)
        y_sl = cv2.getTrackbarPos("YEL S-Low",  TUNER_WIN)
        y_vl = cv2.getTrackbarPos("YEL V-Low",  TUNER_WIN)
        p_hl = cv2.getTrackbarPos("PNK H-Low",  TUNER_WIN)
        p_hh = cv2.getTrackbarPos("PNK H-High", TUNER_WIN)
        p_sl = cv2.getTrackbarPos("PNK S-Low",  TUNER_WIN)
        p_vl = cv2.getTrackbarPos("PNK V-Low",  TUNER_WIN)
        lower_y = np.array([y_hl, y_sl, y_vl], dtype=np.uint8)
        upper_y = np.array([y_hh, 255,  255 ], dtype=np.uint8)
        lower_p = np.array([p_hl, p_sl, p_vl], dtype=np.uint8)
        upper_p = np.array([p_hh, 255,  255 ], dtype=np.uint8)
    except cv2.error:
        pass
    return lower_y, upper_y, lower_p, upper_p


def main():
    stream = CameraStream(CAMERA_INDEX)
    if not stream.cap.isOpened():
        print(f"[ERROR] Cannot open camera {CAMERA_INDEX}.")
        print("        Make sure the Camo desktop app is running.")
        print("        Try CAMERA_INDEX = 1 or 2.")
        sys.exit(1)

    stream.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    stream.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[INFO] Camera ready.  Q = quit  |  C = open color tuner")

    lower_y, upper_y = YELLOW_LOWER.copy(), YELLOW_UPPER.copy()
    lower_p, upper_p = PINK_LOWER.copy(),   PINK_UPPER.copy()
    tuner_open  = False
    frame_count = 0

    while True:
        ret, frame = stream.read()
        if not ret:
            continue

        frame_count += 1

        # Update from tuner
        if tuner_open:
            lower_y, upper_y, lower_p, upper_p = read_tuner(lower_y, upper_y,
                                                              lower_p, upper_p)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ── Build masks ────────────────────────────────────────────────────
        mask_yellow = cv2.inRange(hsv, lower_y, upper_y)
        mask_pink   = cv2.inRange(hsv, lower_p, upper_p)

        # ── Detect objects ─────────────────────────────────────────────────
        yellow_rects = find_objects(mask_yellow)
        pink_rects   = find_objects(mask_pink)

        total = 0

        # 🟡 Yellow = LEGO character / minifigure
        for (x, y, w, h) in yellow_rects:
            dist = estimate_distance(h, LEGO_CHAR_HEIGHT_CM)
            draw_box(frame, x, y, w, h, "LEGO Char", dist)
            if frame_count <= 4 and CALIB_PX is None:
                print(f"[CALIB] Yellow LEGO pixel height = {h}  (set CALIB_PX={h})")
            total += 1

        # 🟪 Pink = LEGO object / thing
        for (x, y, w, h) in pink_rects:
            dist = estimate_distance(h, LEGO_THING_HEIGHT_CM)
            draw_box(frame, x, y, w, h, "person", dist)
            total += 1

        # ── HUD ────────────────────────────────────────────────────────────
        hud = (f"LEGO Char (yellow): {len(yellow_rects)}   "
               f"person: {len(pink_rects)}   "
               f"| Q=quit  C=tune colors")
        cv2.putText(frame, hud, (10, 30),
                    FONT, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # ── Mini mask previews (top-right corner) ──────────────────────────
        h_f, w_f = frame.shape[:2]
        for i, (m, tag, col) in enumerate([
                (mask_yellow, "person", (0, 220, 220)),
                (mask_pink,   "person",   (220, 0, 220))]):
            sm  = cv2.resize(m, (160, 90))
            bgr = cv2.cvtColor(sm, cv2.COLOR_GRAY2BGR)
            x0  = w_f - 175 + (i * -175 if i else 0)   # won't overlap
            x0  = w_f - 340 + i * 175
            frame[10:100, x0:x0+160] = bgr
            cv2.putText(frame, tag, (x0, 112),
                        FONT, 0.45, col, 1, cv2.LINE_AA)

        cv2.imshow("compCV — LEGO Detector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and not tuner_open:
            create_tuner(lower_y, upper_y, lower_p, upper_p)
            tuner_open = True
            print("[INFO] Color tuner opened.")

    stream.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
