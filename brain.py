import pyautogui
import time
import random
import subprocess
import os

# Optional — graceful if not installed
try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# -------------------------------
# GLOBAL SETTINGS
# -------------------------------

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# -------------------------------
# MOUSE CONTROL
# -------------------------------

def move_mouse(x, y, duration=0.3):
    pyautogui.moveTo(x, y, duration=duration)
    return True

def click(x, y):
    pyautogui.click(x, y)
    return True

def double_click(x, y):
    pyautogui.doubleClick(x, y)
    return True

def right_click(x, y):
    pyautogui.rightClick(x, y)
    return True

def drag_to(x, y, duration=0.5):
    pyautogui.dragTo(x, y, duration=duration)
    return True

# -------------------------------
# KEYBOARD CONTROL
# -------------------------------

def type_text(text, interval=0.04):
    """Type text — uses clipboard for special chars, write() for plain ASCII."""
    try:
        # Check if text has special/unicode chars pyautogui.write can't handle
        if all(ord(c) < 128 and c.isprintable() for c in text):
            pyautogui.write(text, interval=interval)
        else:
            # Use clipboard paste — handles ALL characters
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
        return True
    except Exception as e:
        print("type_text error:", e)
        # Last resort fallback
        pyautogui.write(text, interval=interval)
        return True

def press_key(key):
    pyautogui.press(key)
    return True

def hotkey(*keys):
    pyautogui.hotkey(*keys)
    return True

def press_any_key(command):
    try:
        key = command.replace("press ", "").strip().lower()
        pyautogui.press(key)
        return True
    except Exception as e:
        print("Key error:", e)
        return False

def press_combo(command):
    try:
        keys = command.replace("press ", "").strip().lower().split()
        pyautogui.hotkey(*keys)
        return True
    except Exception as e:
        print("Combo error:", e)
        return False

# -------------------------------
# SCROLL
# -------------------------------

def scroll(direction="down", amount=500):
    pyautogui.scroll(amount if direction == "up" else -amount)
    return True

# -------------------------------
# VOLUME CONTROL
# -------------------------------

def volume_up():
    pyautogui.press("volumeup")
    return True

def volume_down():
    pyautogui.press("volumedown")
    return True

def mute():
    pyautogui.press("volumemute")
    return True

def set_volume(level):
    """Set volume to a specific level 0-100 using nircmd if available."""
    try:
        # nircmd way (most reliable on Windows)
        val = int(65535 * int(level) / 100)
        subprocess.run(["nircmd", "setsysvolume", str(val)], check=True)
        return True
    except Exception:
        # Fallback: press keys approximate number of times
        mute()
        time.sleep(0.1)
        mute()
        presses = int(level / 2)
        for _ in range(50):  # reset to 0 first
            pyautogui.press("volumedown")
        for _ in range(presses):
            pyautogui.press("volumeup")
        return True

# -------------------------------
# BRIGHTNESS CONTROL
# -------------------------------

def brightness_up(step=10):
    if SBC_AVAILABLE:
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(100, current + step))
            return True
        except Exception:
            pass
    # Fallback: keyboard shortcut (works on some laptops)
    pyautogui.hotkey("fn", "f6")
    return True

def brightness_down(step=10):
    if SBC_AVAILABLE:
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(0, current - step))
            return True
        except Exception:
            pass
    pyautogui.hotkey("fn", "f5")
    return True

def set_brightness(level):
    if SBC_AVAILABLE:
        try:
            sbc.set_brightness(max(0, min(100, int(level))))
            return True
        except Exception:
            pass
    return False

# -------------------------------
# WINDOW CONTROL
# -------------------------------

def close_window():
    """Close the current active window."""
    pyautogui.hotkey("alt", "f4")
    return True

def close_tab():
    """Close current browser/editor tab."""
    pyautogui.hotkey("ctrl", "w")
    return True

def minimize_window():
    """Minimize the current window."""
    pyautogui.hotkey("win", "down")
    return True

def maximize_window():
    """Maximize the current window."""
    pyautogui.hotkey("win", "up")
    return True

def restore_window():
    """Restore window — works from both maximized and minimized."""
    import subprocess
    # Try PowerShell to restore properly first
    try:
        subprocess.run([
            "powershell", "-Command",
            "$sig = '[DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);';"
            "$type = Add-Type -MemberDefinition $sig -Name Win -Namespace NativeMethods -PassThru;"
            "$hwnd = (Get-Process | Where-Object {$_.MainWindowTitle -ne \"\"} | Select-Object -First 1).MainWindowHandle;"
            "$type::ShowWindow($hwnd, 9)"  # SW_RESTORE = 9
        ], capture_output=True, timeout=3)
        return True
    except Exception:
        pass
    # Fallback: win+shift+m restores all minimized windows
    pyautogui.hotkey("win", "shift", "m")
    return True

def snap_left():
    """Snap window to left half of screen."""
    pyautogui.hotkey("win", "left")
    return True

def snap_right():
    """Snap window to right half of screen."""
    pyautogui.hotkey("win", "right")
    return True

def switch_window():
    """Alt+Tab to switch between windows."""
    pyautogui.hotkey("alt", "tab")
    return True

def switch_window_back():
    """Alt+Shift+Tab to switch backwards."""
    pyautogui.hotkey("alt", "shift", "tab")
    return True

def show_all_windows():
    """Win+Tab — Task View."""
    pyautogui.hotkey("win", "tab")
    return True

def minimize_all():
    """Win+D — show desktop (minimize all)."""
    pyautogui.hotkey("win", "d")
    return True

def restore_all():
    """Win+D again — restore all minimized windows."""
    pyautogui.hotkey("win", "d")
    return True

def new_virtual_desktop():
    """Create a new virtual desktop."""
    pyautogui.hotkey("win", "ctrl", "d")
    return True

def close_virtual_desktop():
    """Close current virtual desktop."""
    pyautogui.hotkey("win", "ctrl", "f4")
    return True

def next_virtual_desktop():
    """Switch to next virtual desktop."""
    pyautogui.hotkey("win", "ctrl", "right")
    return True

def prev_virtual_desktop():
    """Switch to previous virtual desktop."""
    pyautogui.hotkey("win", "ctrl", "left")
    return True

# -------------------------------
# TAB CONTROL (browsers/editors)
# -------------------------------

def new_tab():
    pyautogui.hotkey("ctrl", "t")
    return True

def reopen_tab():
    """Reopen last closed tab."""
    pyautogui.hotkey("ctrl", "shift", "t")
    return True

def next_tab():
    pyautogui.hotkey("ctrl", "tab")
    return True

def prev_tab():
    pyautogui.hotkey("ctrl", "shift", "tab")
    return True

def go_to_tab(n):
    """Go to tab number 1-8."""
    n = max(1, min(8, int(n)))
    pyautogui.hotkey("ctrl", str(n))
    return True

# -------------------------------
# BROWSER CONTROL
# -------------------------------

def go_back():
    pyautogui.hotkey("alt", "left")
    return True

def go_forward():
    pyautogui.hotkey("alt", "right")
    return True

def refresh_page():
    pyautogui.hotkey("ctrl", "r")
    return True

def hard_refresh():
    pyautogui.hotkey("ctrl", "shift", "r")
    return True

def open_new_window():
    pyautogui.hotkey("ctrl", "n")
    return True

def open_incognito():
    pyautogui.hotkey("ctrl", "shift", "n")
    return True

def zoom_in():
    pyautogui.hotkey("ctrl", "=")
    return True

def zoom_out():
    pyautogui.hotkey("ctrl", "-")
    return True

def zoom_reset():
    pyautogui.hotkey("ctrl", "0")
    return True

def open_url(url):
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.3)
    pyautogui.write(url, interval=0.03)
    pyautogui.press("enter")
    return True

# -------------------------------
# FILE OPERATIONS
# -------------------------------

def copy():
    pyautogui.hotkey("ctrl", "c")
    return True

def cut():
    pyautogui.hotkey("ctrl", "x")
    return True

def paste():
    pyautogui.hotkey("ctrl", "v")
    return True

def undo():
    pyautogui.hotkey("ctrl", "z")
    return True

def redo():
    pyautogui.hotkey("ctrl", "y")
    return True

def select_all():
    pyautogui.hotkey("ctrl", "a")
    return True

def save_file():
    pyautogui.hotkey("ctrl", "s")
    return True

def save_as():
    pyautogui.hotkey("ctrl", "shift", "s")
    return True

def open_file():
    pyautogui.hotkey("ctrl", "o")
    return True

def find_in_page():
    pyautogui.hotkey("ctrl", "f")
    return True

def print_page():
    pyautogui.hotkey("ctrl", "p")
    return True

# -------------------------------
# SCREENSHOT / SNIP
# -------------------------------

def screenshot():
    pyautogui.press("printscreen")
    return True

def screenshot_window():
    pyautogui.hotkey("alt", "printscreen")
    return True

def snip():
    pyautogui.hotkey("win", "shift", "s")
    return True

# -------------------------------
# APPLICATION CONTROL
# -------------------------------
def open_app(app_name):
    try:
        import pyperclip

        app_name = app_name.lower().strip().strip(".,!?;:'\"")

        # Normalize spoken names
        name_map = {
            "google chrome":      "chrome",
            "microsoft edge":     "edge",
            "visual studio code": "vscode",
            "command prompt":     "cmd",
            "file explorer":      "explorer",
            "vs code":            "vscode",
            "word":               "microsoft word",
            "excel":              "microsoft excel",
            "powerpoint":         "microsoft powerpoint",
        }
        app_name = name_map.get(app_name, app_name)

        print(f"🔍 Searching Windows for: {app_name}")

        # Close any open start menu first
        pyautogui.press("escape")
        time.sleep(0.2)

        # Open Windows search
        pyautogui.press("win")
        time.sleep(1.0)  # wait for search box to appear

        # Use clipboard paste — works for ALL app names reliably
        pyperclip.copy(app_name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.2)  # wait for search results

        # Press enter to open top result
        pyautogui.press("enter")
        time.sleep(1.5)

        print(f"Opened: {app_name}")
        return True

    except Exception as e:
        print(" Open app error:", e)
        return False

def close_app(app_name):
    """Force-close an app by process name."""
    if PSUTIL_AVAILABLE:
        app_name = app_name.lower().strip()
        process_map = {
            "chrome": "chrome.exe",
            "brave": "brave.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "notepad": "notepad.exe",
            "calculator": "calculatorapp.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "teams": "teams.exe",
            "vlc": "vlc.exe",
            "zoom": "zoom.exe",
        }
        proc_name = process_map.get(app_name, f"{app_name}.exe")
        killed = False
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"].lower() == proc_name.lower():
                proc.kill()
                killed = True
        if killed:
            print(f"Killed {proc_name}")
            return True

    # Fallback: alt+f4 on active window
    close_window()
    return True

# -------------------------------
# SYSTEM CONTROL
# -------------------------------

DANGEROUS = ["shutdown", "restart", "sign out", "hibernate"]

def confirm(command):
    if any(d in command for d in DANGEROUS):
        ans = input(f"⚠️ Confirm '{command}'? (y/n): ")
        return ans.lower() == "y"
    return True

def shutdown():
    if confirm("shutdown"):
        subprocess.run(["shutdown", "/s", "/t", "5"])
        return True
    return False

def restart():
    if confirm("restart"):
        subprocess.run(["shutdown", "/r", "/t", "5"])
        return True
    return False

def sleep():
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    return True

def hibernate():
    if confirm("hibernate"):
        subprocess.run(["shutdown", "/h"])
        return True
    return False

def sign_out():
    if confirm("sign out"):
        subprocess.run(["shutdown", "/l"])
        return True
    return False

def lock():
    pyautogui.hotkey("win", "l")
    return True

def cancel_shutdown():
    """Cancel a scheduled shutdown."""
    subprocess.run(["shutdown", "/a"])
    return True

def open_task_manager():
    pyautogui.hotkey("ctrl", "shift", "esc")
    return True

def empty_recycle_bin():
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        return True
    except Exception:
        subprocess.run(["PowerShell", "-Command",
                        "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"])
        return True

# -------------------------------
# CLIPBOARD
# -------------------------------

def get_clipboard():
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return ""

def set_clipboard(text):
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False

# -------------------------------
# HUMAN DELAY
# -------------------------------

def human_delay(min_t=0.3, max_t=0.8):
    time.sleep(random.uniform(min_t, max_t))

def normalize(cmd):
    return cmd.lower().strip()

# -------------------------------
# EXECUTE ACTION (for brain.py)
# -------------------------------

def execute_action(action):
    if not action:
        return False

    cmd    = action.get("action", "")
    target = action.get("target", "")
    text   = action.get("text", "")
    key    = action.get("key", "")
    level  = action.get("level", None)

    try:
        # App control
        if cmd == "open_app":           return open_app(target)
        elif cmd == "close_app":        return close_app(target)

        # Text / keys
        elif cmd == "type":             return type_text(text)
        elif cmd == "press_key":        return press_key(key)
        elif cmd == "hotkey":           return hotkey(*key.split("+"))

        # Window
        elif cmd == "close_window":     return close_window()
        elif cmd == "minimize":         return minimize_window()
        elif cmd == "maximize":         return maximize_window()
        elif cmd == "restore":          return restore_window()
        elif cmd == "snap_left":        return snap_left()
        elif cmd == "snap_right":       return snap_right()
        elif cmd == "switch_window":    return switch_window()
        elif cmd == "minimize_all":     return minimize_all()
        elif cmd == "show_desktop":     return minimize_all()

        # Tabs
        elif cmd == "new_tab":          return new_tab()
        elif cmd == "close_tab":        return close_tab()
        elif cmd == "next_tab":         return next_tab()
        elif cmd == "prev_tab":         return prev_tab()
        elif cmd == "reopen_tab":       return reopen_tab()

        # Browser
        elif cmd == "go_back":          return go_back()
        elif cmd == "go_forward":       return go_forward()
        elif cmd == "refresh":          return refresh_page()
        elif cmd == "open_url":         return open_url(target)
        elif cmd == "zoom_in":          return zoom_in()
        elif cmd == "zoom_out":         return zoom_out()
        elif cmd == "zoom_reset":       return zoom_reset()
        elif cmd == "incognito":        return open_incognito()

        # File ops
        elif cmd == "copy":             return copy()
        elif cmd == "cut":              return cut()
        elif cmd == "paste":            return paste()
        elif cmd == "undo":             return undo()
        elif cmd == "redo":             return redo()
        elif cmd == "select_all":       return select_all()
        elif cmd == "save":             return save_file()
        elif cmd == "find":             return find_in_page()

        # Screenshot
        elif cmd == "screenshot":       return screenshot()
        elif cmd == "snip":             return snip()

        # Volume
        elif cmd == "volume_up":        return volume_up()
        elif cmd == "volume_down":      return volume_down()
        elif cmd == "mute":             return mute()
        elif cmd == "set_volume":       return set_volume(level or 50)

        # Brightness
        elif cmd == "brightness_up":    return brightness_up()
        elif cmd == "brightness_down":  return brightness_down()
        elif cmd == "set_brightness":   return set_brightness(level or 50)

        # System
        elif cmd == "lock":             return lock()
        elif cmd == "sleep":            return sleep()
        elif cmd == "shutdown":         return shutdown()
        elif cmd == "restart":          return restart()
        elif cmd == "task_manager":     return open_task_manager()
        elif cmd == "scroll":           return scroll(target)

        return False

    except Exception as e:
        print("Execution error:", e)
        return False

# -------------------------------
# NATURAL COMMAND EXECUTOR
# -------------------------------

def execute_command(command):
    command = normalize(command)

    try:
        # Keys
        if command.startswith("press "):
            words = command.split()
            return press_any_key(command) if len(words) == 2 else press_combo(command)
        elif command.startswith("type "):
            return type_text(command.replace("type ", "", 1))

        # Volume
        elif "volume up" in command:        return volume_up()
        elif "volume down" in command:      return volume_down()
        elif "mute" in command:             return mute()

        # Brightness
        elif "brightness up" in command:    return brightness_up()
        elif "brightness down" in command:  return brightness_down()

        # Window management
        elif "close window" in command:     return close_window()
        elif "close tab" in command:        return close_tab()
        elif "minimize" in command:         return minimize_window()
        elif "maximize" in command:         return maximize_window()
        elif "restore" in command:          return restore_window()
        elif "snap left" in command:        return snap_left()
        elif "snap right" in command:       return snap_right()
        elif "show desktop" in command:     return minimize_all()
        elif "switch window" in command:    return switch_window()
        elif "task view" in command:        return show_all_windows()

        # Virtual desktops
        elif "new desktop" in command:      return new_virtual_desktop()
        elif "next desktop" in command:     return next_virtual_desktop()
        elif "previous desktop" in command: return prev_virtual_desktop()
        elif "close desktop" in command:    return close_virtual_desktop()

        # Tabs
        elif "new tab" in command:          return new_tab()
        elif "reopen tab" in command:       return reopen_tab()
        elif "next tab" in command:         return next_tab()
        elif "previous tab" in command:     return prev_tab()

        # Browser
        elif "go back" in command:          return go_back()
        elif "go forward" in command:       return go_forward()
        elif "refresh" in command:          return refresh_page()
        elif "zoom in" in command:          return zoom_in()
        elif "zoom out" in command:         return zoom_out()
        elif "incognito" in command:        return open_incognito()

        # File ops
        elif "copy" in command:             return copy()
        elif "paste" in command:            return paste()
        elif "cut" in command:              return cut()
        elif "undo" in command:             return undo()
        elif "redo" in command:             return redo()
        elif "select all" in command:       return select_all()
        elif "save" in command:             return save_file()
        elif "find" in command:             return find_in_page()

        # Screenshot
        elif "screenshot" in command:       return screenshot()
        elif "snip" in command:             return snip()

        # App
        elif command.startswith("open "):
            return open_app(command.replace("open ", "", 1))
        elif command.startswith("close "):
            target = command.replace("close ", "", 1)
            if target in ("window",):
                return close_window()
            return close_app(target)

        # Scroll
        elif "scroll up" in command:        return scroll("up")
        elif "scroll down" in command:      return scroll("down")

        # System
        elif "lock" in command:             return lock()
        elif "sleep" in command:            return sleep()
        elif "shutdown" in command:         return shutdown()
        elif "restart" in command:          return restart()
        elif "task manager" in command:     return open_task_manager()
        elif "empty recycle" in command:    return empty_recycle_bin()

        else:
            print("Unknown command:", command)
            return False

    except Exception as e:
        print("Execution error:", e)
        return False


if __name__ == "__main__":
    print("Starting test in 3 seconds...")
    time.sleep(3)
    execute_command("open notepad")
    time.sleep(1)
    execute_command("type your ai agent is working perfectly")
    execute_command("press enter")
    execute_command("volume up")
    execute_command("brightness up")
    print("ALL WORKING!")