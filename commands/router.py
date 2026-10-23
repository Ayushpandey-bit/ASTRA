"""
ASTRA command handlers for Windows.
Keeps the existing try_handle_command(text) interface used by astra.py.
"""
import os
import re
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus

try:
    import winsound
except ImportError:  # Non-Windows fallback
    winsound = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTES_FILE = os.path.join(BASE_DIR, "astra_notes.txt")
_timer_lock = threading.Lock()
_active_timers = []


def _notify(title, message):
    """Background timer notification; avoids calling pyttsx3 from another thread."""
    print(f"\n[ASTRA NOTIFICATION] {title}: {message}\n")
    if winsound:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


def _start_timer(seconds, message, title="Timer finished"):
    def finish():
        time.sleep(seconds)
        _notify(title, message)

    thread = threading.Thread(target=finish, daemon=True)
    thread.start()
    with _timer_lock:
        _active_timers.append(thread)


def _open_app(app_name):
    apps = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "calc": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "command prompt": ["cmd.exe"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe"],
        "task manager": ["taskmgr.exe"],
        "file explorer": ["explorer.exe"],
        "explorer": ["explorer.exe"],
        "vscode": ["code"],
        "vs code": ["code"],
        "visual studio code": ["code"],
    }
    key = app_name.lower().strip()
    if key in apps:
        try:
            subprocess.Popen(apps[key], shell=False)
            return f"Opening {app_name}."
        except (OSError, subprocess.SubprocessError):
            return f"I couldn't open {app_name}. Check that it is installed and available on PATH."

    # Common websites are handled separately. Do not pass arbitrary spoken text to a shell.
    folders = {
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    }
    if key in folders:
        try:
            os.startfile(folders[key])
            return f"Opening your {key} folder."
        except (OSError, AttributeError):
            return f"I couldn't open your {key} folder."

    websites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "chatgpt": "https://chatgpt.com",
        "stackoverflow": "https://stackoverflow.com",
    }
    if key in websites:
        webbrowser.open(websites[key])
        return f"Opening {key}."

    return None


def _web_search(text_lower):
    patterns = [
        (r"^(?:please )?search (?:google )?for (.+)$", "google"),
        (r"^(?:please )?search the web for (.+)$", "google"),
        (r"^(?:please )?google (.+)$", "google"),
        (r"^(?:please )?search youtube for (.+)$", "youtube"),
        (r"^(?:please )?youtube search (.+)$", "youtube"),
    ]
    for pattern, engine in patterns:
        match = re.match(pattern, text_lower.strip())
        if match:
            query = match.group(1).strip()
            if not query:
                return "What would you like me to search for?"
            base = "https://www.youtube.com/results?search_query=" if engine == "youtube" else "https://www.google.com/search?q="
            webbrowser.open(base + quote_plus(query))
            return f"Searching {engine.title()} for {query}."
    return None


def _productivity_command(text, lower):
    if re.search(r"\bwhat time is it\b|\btell me the time\b|\bcurrent time\b", lower):
        return f"It's {datetime.now().strftime('%I:%M %p')}."
    if re.search(r"\bwhat(?:'s| is) the date\b|\btoday'?s date\b|\bwhat day is it\b", lower):
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

    timer_match = re.search(r"\b(?:set )?(?:a )?timer for (\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b", lower)
    if timer_match:
        amount = int(timer_match.group(1))
        unit = timer_match.group(2)
        multiplier = 3600 if unit.startswith(("hour", "hr")) else 60 if unit.startswith(("minute", "min")) else 1
        seconds = amount * multiplier
        if seconds <= 0 or seconds > 24 * 3600:
            return "Please choose a timer between 1 second and 24 hours."
        _start_timer(seconds, f"Your {amount} {unit} timer has finished.")
        return f"Timer set for {amount} {unit}."

    reminder_match = re.search(r"\bremind me in (\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\s+to\s+(.+)", lower)
    if reminder_match:
        amount = int(reminder_match.group(1))
        unit = reminder_match.group(2)
        reminder_text = reminder_match.group(3).strip()
        multiplier = 3600 if unit.startswith(("hour", "hr")) else 60 if unit.startswith(("minute", "min")) else 1
        seconds = amount * multiplier
        if seconds <= 0 or seconds > 7 * 24 * 3600:
            return "Please choose a reminder between 1 second and 7 days."
        _start_timer(seconds, reminder_text, title="Reminder")
        return f"I'll remind you in {amount} {unit} to {reminder_text}."

    if lower.startswith(("take a note ", "note that ", "write a note ")):
        note = re.sub(r"^(take a note|note that|write a note)\s*", "", text, flags=re.I).strip()
        if not note:
            return "What would you like me to write in the note?"
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {note}\n")
        return "I've saved your note."

    if "read my notes" in lower or "show my notes" in lower:
        if not os.path.exists(NOTES_FILE):
            return "You don't have any saved notes yet."
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return "You don't have any saved notes yet."
        # Keep speech concise; latest three notes only.
        return "Your latest notes are: " + " ".join(line.split("] ", 1)[-1].strip() for line in lines[-3:])
    return None


def _system_command(lower):
    if any(phrase in lower for phrase in ("increase volume", "volume up", "turn up the volume")):
        return _press_media_key(0xAF, "Increasing volume.")
    if any(phrase in lower for phrase in ("decrease volume", "volume down", "turn down the volume")):
        return _press_media_key(0xAE, "Decreasing volume.")
    if any(phrase in lower for phrase in ("mute system", "mute the system", "mute volume", "unmute system", "unmute the system")):
        return _press_media_key(0xAD, "Toggling mute.")
    if "take a screenshot" in lower or "capture screenshot" in lower or "screenshot" == lower.strip():
        try:
            from PIL import ImageGrab
            path = os.path.join(BASE_DIR, f"astra_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            ImageGrab.grab().save(path)
            return f"Screenshot saved to {os.path.basename(path)} in the ASTRA folder."
        except ImportError:
            return "Screenshot needs Pillow installed. Run pip install pillow."
        except Exception:
            return "I couldn't take a screenshot."
    if "check my battery" in lower or "battery status" in lower or "battery level" in lower:
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is None:
                return "I couldn't read battery status on this device."
            state = "charging" if battery.power_plugged else "not charging"
            return f"Battery is at {round(battery.percent)} percent and {state}."
        except ImportError:
            return "Battery status needs psutil installed. Run pip install psutil."
        except Exception:
            return "I couldn't read battery status."
    return None


def _press_media_key(vk, response):
    if os.name != "nt":
        return "System volume controls are currently supported on Windows only."
    try:
        import ctypes
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        return response
    except Exception:
        return "I couldn't change the system volume."


def try_handle_command(text):
    """Return a response string for supported commands, otherwise None for AI chat."""
    if not text or not text.strip():
        return None
    text_lower = text.lower().strip()

    result = _web_search(text_lower)
    if result:
        return result

    result = _productivity_command(text, text_lower)
    if result:
        return result

    result = _system_command(text_lower)
    if result:
        return result

    # Match "open X" at the beginning to avoid accidentally opening apps
    # when a general question merely mentions the word "open".
    match = re.match(r"^(?:please )?open\s+(.+?)\s*[.!?]*$", text_lower)
    if match:
        app_name = match.group(1).strip()
        # Remove common polite suffixes from speech transcription.
        app_name = re.sub(r"\s+(please|for me)$", "", app_name)
        return _open_app(app_name) or f"I don't know how to open {app_name} yet."

    return None
