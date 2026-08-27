import subprocess
def open_app(app_name):
    try:
        subprocess.Popen(f"start {app_name}", shell=True)
        return f"Opening {app_name}"
    except Exception as e:
        return f"Sorry, I couldn't open {app_name}. Error: {e}"

# --- Command router: fuzzy-matches "open X" anywhere in the sentence ---
def try_handle_command(text):
    text_lower = text.lower()

    app_map = {
        "notepad": "notepad",
        "chrome": "chrome",
        "calculator": "calc",
        "paint": "mspaint",
        "word": "winword",
        "excel": "excel",
    }

    if "open" in text_lower:
        for keyword, exe in app_map.items():
            if keyword in text_lower:
                return open_app(exe)

    return None 