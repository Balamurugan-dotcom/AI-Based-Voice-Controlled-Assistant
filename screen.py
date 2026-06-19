import cv2
import numpy as np
import pytesseract
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------
# CONFIG
# -------------------------------

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\kruth\Downloads\VoiceAssistant\New folder\tesseract.exe"

# -------------------------------
# VERIFY TESSERACT
# -------------------------------

def check_tesseract():
    try:
        print("Tesseract Version:", pytesseract.get_tesseract_version())
    except:
        print(" Tesseract NOT working")

# -------------------------------
# IoU + NMS
# -------------------------------

def _iou(a, b):
    ax1, ay1 = a["x"], a["y"]
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1 = b["x"], b["y"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    if inter == 0:
        return 0.0
    union = (ax2-ax1)*(ay2-ay1) + (bx2-bx1)*(by2-by1) - inter
    return inter / max(union, 1)

def _nms(items, iou_thresh=0.45):
    items = sorted(items, key=lambda x: x["conf"], reverse=True)
    kept = []
    for c in items:
        if not any(_iou(c, k) > iou_thresh for k in kept):
            kept.append(c)
    return kept

# -------------------------------
# SINGLE TESSERACT PASS
# -------------------------------

def _tess_pass(img_variant, psm, scale_x, scale_y):
    try:
        data = pytesseract.image_to_data(
            img_variant,
            config=f"--oem 3 --psm {psm}",
            output_type=pytesseract.Output.DICT
        )
    except Exception:
        return []

    results = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        try:
            conf = int(data["conf"][i])
        except (ValueError, TypeError):
            continue

        if conf < 55 or len(text) < 2:
            continue

        # Keep alphanumeric + useful symbols only
        clean = ''.join(c for c in text if c.isalnum() or c in " .,!?@#$%&()_-:/\\|+=<>[]{}\"'`~^")
        if len(clean) < 2:
            continue

        # Must be mostly real characters, not symbol soup
        alpha_ratio = sum(c.isalnum() or c == ' ' for c in clean) / len(clean)
        if alpha_ratio < 0.5:
            continue

        w = int(data["width"][i] * scale_x)
        h = int(data["height"][i] * scale_y)
        if w <= 0 or h <= 0:
            continue

        results.append({
            "text": clean,
            "x": int(data["left"][i] * scale_x),
            "y": int(data["top"][i] * scale_y),
            "w": w, "h": h,
            "conf": conf / 100.0,
            "source": "tesseract"
        })
    return results

# -------------------------------
# ICON / BUTTON DETECTION
# -------------------------------

def _detect_icons(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, None, fx=0.5, fy=0.5)
    edges = cv2.Canny(cv2.GaussianBlur(small, (5, 5), 0), 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_area = small.shape[0] * small.shape[1]
    sx = image.shape[1] / small.shape[1]
    sy = image.shape[0] / small.shape[0]
    icons = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100 or area > img_area * 0.04:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if not (0.5 <= w / max(h, 1) <= 2.0):
            continue
        icons.append({
            "text": f"icon_{int(w*sx)}x{int(h*sy)}",
            "x": int(x*sx), "y": int(y*sy),
            "w": int(w*sx), "h": int(h*sy),
            "conf": 0.7, "source": "icon"
        })

    return _nms(icons, iou_thresh=0.5)

# -------------------------------
# EDIT DISTANCE
# -------------------------------

def _edit_distance(a, b):
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[:], i
        for j in range(1, n + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev[j-1] + cost)
    return dp[n]

# -------------------------------
# MAIN OCR — Tesseract only, tuned for 1920x1080
# -------------------------------

def extract_text(image):
    original_h, original_w = image.shape[:2]

    # — Build the 3 winning variants on the FULL 1920x1080 image —
    # Your data shows: gray > clahe > otsu  (thresh/inverted are bad, skip them)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # — Also run 1.5x upscale for small text (taskbar icons, tooltips) —
    # Only on gray+clahe (best two), skip otsu at upscale (redundant)
    up = cv2.resize(image, None, fx=1.25, fy=1.25)
    up_gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    up_clahe = clahe.apply(up_gray)
    up_sx = original_w / up.shape[1]
    up_sy = original_h / up.shape[0]

    # — Task list —
    # Full res: gray+psm11, gray+psm6, clahe+psm11, clahe+psm6, otsu+psm11
    # Upscaled: up_gray+psm11, up_clahe+psm11
    # Total: 7 passes — fast, parallel, no EasyOCR
    tasks = [
        # Full resolution — best performers from your data
        (gray,     11, 1.0, 1.0),   # 185 items — top performer
        (gray,      6, 1.0, 1.0),   # 147 items
        (enhanced, 11, 1.0, 1.0),   # 182 items
        (enhanced,  6, 1.0, 1.0),   # 149 items
        (otsu,     11, 1.0, 1.0),   # 177 items — catches what gray misses
        # Upscaled — catches small text gray misses at full res
        (up_gray,  11, up_sx, up_sy),
        (up_clahe, 11, up_sx, up_sy),
    ]

    all_results = []

    with ThreadPoolExecutor(max_workers=8) as pool:
        tess_futures = [pool.submit(_tess_pass, v, psm, sx, sy) for v, psm, sx, sy in tasks]
        icon_future  = pool.submit(_detect_icons, image)

        for f in as_completed(tess_futures):
            all_results.extend(f.result())

        icon_results = icon_future.result()

    final_text = _nms(all_results, iou_thresh=0.45)
    final = final_text + icon_results

    return final

# -------------------------------
# SMART MATCHING
# -------------------------------

def find_best_match(target, ocr_data):
    target = target.lower()
    best, best_score = None, 0.0

    for item in ocr_data:
        text = item["text"].lower()
        if text == target:
            return item
        if target in text:
            score = 0.9 * (len(target) / len(text)) + 0.1
        else:
            dist = _edit_distance(target, text)
            score = 1.0 - dist / max(len(target), len(text))
        if score > best_score:
            best_score = score
            best = item

    return best if best_score > 0.45 else None

# -------------------------------
# CENTER POINT
# -------------------------------

def get_center(item):
    return (item["x"] + item["w"] // 2, item["y"] + item["h"] // 2)

# -------------------------------
# DEBUG IMAGE
# -------------------------------

def draw_boxes(image, ocr_data, save_path="debug.png"):
    img = image.copy()
    color_map = {
        "tesseract": (0, 255, 0),
        "icon":      (0, 128, 255)
    }
    for item in ocr_data:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = color_map.get(item.get("source", "tesseract"), (200, 200, 200))
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, f"{item['text']} ({item['conf']:.2f})",
                    (x, max(y - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    cv2.imwrite(save_path, img)
    print(f"Debug image saved: {save_path}")
    return img

# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    from screen import capture_screen

    print("🚀 OCR — Tesseract-only, tuned for 1920x1080")
    check_tesseract()

    start = time.time()
    img = capture_screen()

    t1 = time.time()
    ocr_data = extract_text(img)
    t2 = time.time()

    text_items = [x for x in ocr_data if x.get("source") == "tesseract"]
    icon_items = [x for x in ocr_data if x.get("source") == "icon"]

    print(f"\n📊 Total   : {len(ocr_data)}")
    print(f"   📝 Text  : {len(text_items)}")
    print(f"   🔲 Icons : {len(icon_items)}")
    print(f"⏱  OCR time: {t2 - t1:.2f}s")
    print(f"⏱  Total   : {t2 - start:.2f}s\n")

    for i, item in enumerate(ocr_data, 1):
        tag = "🔲" if item.get("source") == "icon" else "📝"
        print(f"{i:3}. {tag} conf={item['conf']:.2f}  '{item['text']}'  @ ({item['x']},{item['y']})")

    match = find_best_match("chrome", ocr_data)
    if match:
        cx, cy = get_center(match)
        print(f"\n🎯 'chrome' → ({cx}, {cy})  conf={match['conf']:.2f}")
    else:
        print("\n 'chrome' not found")

    draw_boxes(img, ocr_data)
    print(f"\n⏱ Total: {t2 - start:.2f}s")