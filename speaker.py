import pyautogui
import numpy as np
import cv2
import time
import hashlib

# -------------------------------
# BASIC SCREEN FUNCTIONS
# -------------------------------

def capture_screen(gray=False):
    """
    Capture full screen (BGR or Gray)
    """
    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if gray:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return img


def capture_region(x, y, width, height, gray=False):
    """
    Capture specific region
    """
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if gray:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return img


def get_screen_size():
    """
    Return width, height
    """
    width, height = pyautogui.size()
    return width, height


def save_screen(filename="screen.png"):
    pyautogui.screenshot().save(filename)


def save_region(x, y, width, height, filename="region.png"):
    pyautogui.screenshot(region=(x, y, width, height)).save(filename)


# -------------------------------
# IMAGE PROCESSING
# -------------------------------

def convert_to_gray(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize_image(image, scale=0.5):
    h, w = image.shape[:2]
    return cv2.resize(image, (int(w * scale), int(h * scale)))


def crop_image(image, x, y, w, h):
    return image[y:y + h, x:x + w]


# -------------------------------
# HASHING (FAST CHANGE DETECTION)
# -------------------------------

def get_screen_hash(image):
    return hashlib.sha1(image.tobytes()).hexdigest()


def is_screen_changed(prev_hash, current_image):
    current_hash = get_screen_hash(current_image)
    return (prev_hash != current_hash), current_hash


# -------------------------------
# SMART CROPPING
# -------------------------------

def smart_crop(image, bbox=None, padding=20):
    if bbox is None:
        return image

    x, y, w, h = bbox

    x1 = max(0, int(x - padding))
    y1 = max(0, int(y - padding))
    x2 = min(image.shape[1], int(x + w + padding))
    y2 = min(image.shape[0], int(y + h + padding))

    return image[y1:y2, x1:x2]


# -------------------------------
# DISPLAY (SAFE DEBUG)
# -------------------------------

def show_image(image, title="Debug", wait=1):
    """
    Non-blocking display
    press 'q' to close
    """
    cv2.imshow(title, image)
    if cv2.waitKey(wait) & 0xFF == ord('q'):
        cv2.destroyAllWindows()


# -------------------------------
# PERFORMANCE UTILITY
# -------------------------------

def capture_and_hash(prev_hash=None):
    """
    Capture screen + check change in one call
    """
    img = capture_screen()
    changed, new_hash = is_screen_changed(prev_hash, img)
    return img, changed, new_hash


# -------------------------------
# HUMAN DELAY
# -------------------------------

def wait(seconds=0.3):
    time.sleep(seconds)


# -------------------------------
# TEST
# -------------------------------

if __name__ == "__main__":
    print("Testing screen module...")

    time.sleep(2)

    img = capture_screen()
    print("Captured")

    w, h = get_screen_size()
    print(f"Resolution: {w}x{h}")

    save_screen("test_screen.png")

    small = resize_image(img, 0.5)
   

    while True:
        show_image(small)