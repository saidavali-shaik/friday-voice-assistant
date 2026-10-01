"""
Combined Friday Server — Automation (YouTube, WhatsApp, Instagram, VS Code,
Google, Terminal, File Manager) + Orb state bridge (idle/listening/responding)
All on port 5000.
"""

import json
import os
import subprocess
import webbrowser
import time
import threading
import urllib.parse
import requests
import websocket
from flask import Flask, request, jsonify
from flask_cors import CORS
from pywinauto import Desktop
from pywinauto import Application
from pywinauto.keyboard import send_keys

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:*", "http://localhost:*"]}})

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
CHROME_CANDIDATES = [
    os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

def find_chrome_path():
    for path in CHROME_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return None


CHROME_PATH = find_chrome_path()
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "FridayChromeProfile")
DEBUG_PORT = 9222
DEBUG_URL = f"http://localhost:{DEBUG_PORT}"

FILES_BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents")

WHATSAPP_WINDOW_TITLE_RE = ".*WhatsApp.*"
WHATSAPP_EXE_FALLBACK = os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe")

VSCODE_WINDOW_TITLE_RE = ".*Visual Studio Code.*"
VSCODE_EXE_CANDIDATES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    r"C:\Program Files\Microsoft VS Code\Code.exe",
]

TERMINAL_WINDOW_TITLE_RE = ".*(Windows Terminal|Command Prompt).*"
FILE_EXPLORER_WINDOW_TITLE_RE = ".*File Explorer.*"


def resolve_filename(filename):
    safe_name = os.path.basename(filename)
    return os.path.join(FILES_BASE_DIR, safe_name)


session_lock = threading.Lock()
youtube_session    = {"active": False, "tab_id": None, "ws_url": None, "last_search": None}
whatsapp_web_session = {"active": False, "tab_id": None, "ws_url": None}
instagram_session  = {"active": False, "tab_id": None, "ws_url": None}
google_session     = {"active": False, "tab_id": None, "ws_url": None}

_cmd_id_counter = [0]

# ===========================================================================
# ORB STATE BRIDGE
# ===========================================================================
current_orb_state = {"mode": "idle"}

@app.route("/state", methods=["GET"])
def get_orb_state():
    return jsonify(current_orb_state)

@app.route("/set/<mode>", methods=["POST"])
def set_orb_state(mode):
    if mode in ["idle", "listening", "responding"]:
        current_orb_state["mode"] = mode
    return jsonify(current_orb_state)


# ===========================================================================
# LOW-LEVEL CDP HELPERS
# ===========================================================================
def chrome_is_running():
    try:
        return requests.get(f"{DEBUG_URL}/json/version", timeout=1).status_code == 200
    except requests.exceptions.RequestException:
        return False


def launch_chrome():
    if chrome_is_running():
        return
    if not CHROME_PATH:
        raise RuntimeError("Google Chrome was not found in a standard Windows installation location.")
    subprocess.Popen([
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
    ])
    for _ in range(30):
        if chrome_is_running():
            return
        time.sleep(0.5)
    raise RuntimeError("Chrome did not start with remote debugging in time.")


def open_new_tab(url):
    r = requests.put(f"{DEBUG_URL}/json/new?{url}", timeout=5)
    r.raise_for_status()
    return r.json()


def tab_is_alive(tab_id):
    try:
        tabs = requests.get(f"{DEBUG_URL}/json", timeout=2).json()
        return any(t["id"] == tab_id for t in tabs)
    except requests.exceptions.RequestException:
        return False


def send_cdp_command(ws_url, method, params=None, wait_result=True, timeout=5):
    _cmd_id_counter[0] += 1
    cmd_id = _cmd_id_counter[0]
    payload = {"id": cmd_id, "method": method, "params": params or {}}
    ws = websocket.create_connection(ws_url, timeout=timeout)
    try:
        ws.send(json.dumps(payload))
        if not wait_result:
            return None
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            if msg.get("id") == cmd_id:
                return msg.get("result")
        raise TimeoutError(f"No CDP response for {method} within {timeout}s")
    finally:
        ws.close()


def navigate(ws_url, url):
    send_cdp_command(ws_url, "Page.navigate", {"url": url})


def evaluate(ws_url, expression):
    result = send_cdp_command(ws_url, "Runtime.evaluate", {"expression": expression, "returnByValue": True})
    return result.get("result", {}).get("value") if result else None


def click_selector(ws_url, selector):
    script = f"""
        (function() {{
            const el = document.querySelector({json.dumps(selector)});
            if (el) {{ el.click(); return true; }}
            return false;
        }})();
    """
    return evaluate(ws_url, script)


def press_enter(ws_url):
    for evt in (
        {"type": "rawKeyDown", "windowsVirtualKeyCode": 13, "key": "Enter"},
        {"type": "char", "key": "Enter", "text": "\r"},
        {"type": "keyUp", "windowsVirtualKeyCode": 13, "key": "Enter"},
    ):
        send_cdp_command(ws_url, "Input.dispatchKeyEvent", evt)


def type_text(ws_url, text):
    ws = websocket.create_connection(ws_url, timeout=10)
    try:
        for ch in text:
            for evt in (
                {"type": "keyDown", "text": ch},
                {"type": "char", "text": ch},
                {"type": "keyUp", "text": ch},
            ):
                _cmd_id_counter[0] += 1
                ws.send(json.dumps({"id": _cmd_id_counter[0], "method": "Input.dispatchKeyEvent", "params": evt}))
            time.sleep(0.02)
    finally:
        ws.close()


# ===========================================================================
# GENERIC SESSION + NATIVE WINDOW HELPERS
# ===========================================================================
def ensure_session(session_dict, fresh_url):
    launch_chrome()
    with session_lock:
        if session_dict["active"] and tab_is_alive(session_dict["tab_id"]):
            return False
        tab = open_new_tab(fresh_url)
        session_dict["active"] = True
        session_dict["tab_id"] = tab["id"]
        session_dict["ws_url"] = tab["webSocketDebuggerUrl"]
        return True


def session_alive(session_dict):
    return session_dict["active"] and tab_is_alive(session_dict["tab_id"])


def close_session(session_dict, label):
    with session_lock:
        if not session_dict["active"]:
            return f"{label} was not open"
        try:
            requests.get(f"{DEBUG_URL}/json/close/{session_dict['tab_id']}", timeout=3)
        except requests.exceptions.RequestException:
            pass
        session_dict["active"] = False
        session_dict["tab_id"] = None
        session_dict["ws_url"] = None
        return f"Closed {label}"


def find_installed_exe(candidates):
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def native_window_exists(title_re, timeout=1):
    try:
        Application(backend="uia").connect(title_re=title_re, timeout=timeout)
        return True
    except Exception:
        return False


def get_native_window(title_re, timeout=15):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            uia_app = Application(backend="uia").connect(title_re=title_re, timeout=1)
            window = uia_app.window(title_re=title_re)
            window.set_focus()
            return window
        except Exception as e:
            last_error = e
            time.sleep(0.5)
    raise RuntimeError(f"Window matching '{title_re}' did not appear in time: {last_error}")


# ===========================================================================
# YOUTUBE
# ===========================================================================
@app.route("/youtube/open", methods=["POST"])
def yt_open():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    opened_new = ensure_session(youtube_session, "https://www.youtube.com")
    if query:
        encoded = requests.utils.quote(query)
        navigate(youtube_session["ws_url"], f"https://www.youtube.com/results?search_query={encoded}")
        youtube_session["last_search"] = query
        time.sleep(1.5)
        return jsonify({"status": "ok", "message": f"Opened YouTube and searched for '{query}'"})
    return jsonify({"status": "ok", "message": "Opened YouTube" if opened_new else "YouTube already open"})


@app.route("/youtube/search", methods=["POST"])
def yt_search():
    data = request.get_json(force=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Missing 'query'"}), 400
    ensure_session(youtube_session, "https://www.youtube.com")
    encoded = requests.utils.quote(query)
    navigate(youtube_session["ws_url"], f"https://www.youtube.com/results?search_query={encoded}")
    youtube_session["last_search"] = query
    time.sleep(1.5)
    return jsonify({"status": "ok", "message": f"Searched for '{query}'"})


@app.route("/youtube/play", methods=["POST"])
def yt_play():
    if not session_alive(youtube_session):
        return jsonify({"status": "error", "message": "No active YouTube session."}), 409
    script = """
        (function() {
            const onWatchPage = location.href.includes('/watch');
            if (onWatchPage) {
                const video = document.querySelector('video');
                if (video) { video.play(); return 'resumed'; }
                return 'none';
            }
            const el = document.querySelector('ytd-video-renderer a#video-title, a#thumbnail');
            if (el) { el.click(); return 'selected'; }
            return 'none';
        })();
    """
    result = evaluate(youtube_session["ws_url"], script)
    if result == "none":
        return jsonify({"status": "error", "message": "Nothing to play."}), 404
    time.sleep(1)
    return jsonify({"status": "ok", "message": "Resumed playback" if result == "resumed" else "Playing first result"})


@app.route("/youtube/pause", methods=["POST"])
def yt_pause():
    if not session_alive(youtube_session):
        return jsonify({"status": "error", "message": "No active YouTube session."}), 409
    paused = evaluate(youtube_session["ws_url"],
        "(function(){if(!location.href.includes('/watch'))return false;const v=document.querySelector('video');if(v){v.pause();return true;}return false;})();")
    if not paused:
        return jsonify({"status": "error", "message": "No video currently playing."}), 404
    return jsonify({"status": "ok", "message": "Paused"})


@app.route("/youtube/stop", methods=["POST"])
def yt_stop():
    if not session_alive(youtube_session):
        return jsonify({"status": "error", "message": "No active YouTube session."}), 409
    evaluate(youtube_session["ws_url"], "(function(){const v=document.querySelector('video');if(v)v.pause();})();")
    navigate(youtube_session["ws_url"], "https://www.youtube.com")
    return jsonify({"status": "ok", "message": "Stopped"})


@app.route("/youtube/back", methods=["POST"])
def yt_back():
    if not session_alive(youtube_session):
        return jsonify({"status": "error", "message": "No active YouTube session."}), 409
    evaluate(youtube_session["ws_url"], "window.history.back();")
    return jsonify({"status": "ok", "message": "Went back"})


@app.route("/youtube/close", methods=["POST"])
def yt_close():
    return jsonify({"status": "ok", "message": close_session(youtube_session, "YouTube")})


# ===========================================================================
# OPEN URL (Spotify etc.)
# ===========================================================================
@app.route("/open_url", methods=["POST"])
def open_url():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"status": "error", "message": "Missing 'url'"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"status": "error", "message": "'url' must start with http:// or https://"}), 400
    try:
        webbrowser.open(url)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "ok", "message": f"Opened {url}"})


# ===========================================================================
# WHATSAPP
# ===========================================================================
wa_lock = threading.Lock()


def whatsapp_mode():
    if native_window_exists(WHATSAPP_WINDOW_TITLE_RE):
        return "native"
    if os.path.isfile(WHATSAPP_EXE_FALLBACK):
        return "native"
    return "chrome"


def wa_is_running():
    return native_window_exists(WHATSAPP_WINDOW_TITLE_RE)


def is_phone_number(contact):
    cleaned = contact.strip()
    digits = cleaned[1:] if cleaned.startswith("+") else cleaned
    return digits.isdigit() and len(digits) >= 7


def wa_launch():
    try:
        os.startfile("whatsapp://")
        return
    except OSError:
        pass
    if os.path.isfile(WHATSAPP_EXE_FALLBACK):
        subprocess.Popen([WHATSAPP_EXE_FALLBACK])
    else:
        raise RuntimeError("Could not launch WhatsApp Desktop.")


def wa_get_window(timeout=15):
    return get_native_window(WHATSAPP_WINDOW_TITLE_RE, timeout=timeout)


def wa_open_chat(contact, message=None):
    if not wa_is_running():
        wa_launch()
    uri = f"whatsapp://send?phone={contact}"
    if message:
        uri += f"&text={urllib.parse.quote(message)}"
    os.startfile(uri)
    return wa_get_window()


class ContactNotFoundError(Exception):
    pass


def _find_search_box(window):
    candidates = [c for c in window.descendants(control_type="Edit") if c.is_visible() and c.is_enabled()]
    if not candidates:
        raise RuntimeError("No visible/enabled Edit control found in WhatsApp window")
    exact_names = {"search or start new chat", "search input textbox", "search"}
    for c in candidates:
        if (c.window_text() or "").strip().lower() in exact_names:
            return c
    candidates.sort(key=lambda c: c.rectangle().top)
    return candidates[0]


def open_first_search_result(window, search_box, timeout=5):
    deadline = time.time() + timeout
    list_control_types = ("ListItem", "DataItem", "TreeItem")
    while time.time() < deadline:
        for ctrl_type in list_control_types:
            rows = [r for r in window.descendants(control_type=ctrl_type) if r.is_visible()]
            if rows:
                rows.sort(key=lambda r: r.rectangle().top)
                rows[0].click_input()
                time.sleep(0.5)
                return
        time.sleep(0.3)
    search_bottom = search_box.rectangle().bottom
    candidates = []
    for el in window.descendants():
        try:
            if not el.is_visible():
                continue
            rect = el.rectangle()
            if rect.top <= search_bottom:
                continue
            if 30 <= rect.height() <= 100 and rect.width() > 100:
                candidates.append((rect.top, el))
        except Exception:
            continue
    if candidates:
        candidates.sort(key=lambda pair: pair[0])
        candidates[0][1].click_input()
        time.sleep(0.5)
        return
    try:
        search_box.click_input()
        send_keys("{DOWN}{ENTER}")
        time.sleep(0.5)
        return
    except Exception:
        pass
    raise ContactNotFoundError("no search result found to open")


def wa_native_search_and_open(name):
    if not wa_is_running():
        wa_launch()
    window = wa_get_window()
    deadline = time.time() + 10
    search_box = None
    while time.time() < deadline:
        try:
            search_box = _find_search_box(window)
            break
        except Exception:
            time.sleep(0.5)
    if search_box is None:
        raise RuntimeError("WhatsApp search box did not become available in time")
    search_box.click_input()
    search_box.set_edit_text("")
    time.sleep(0.2)
    search_box.set_edit_text(name)
    time.sleep(1.5)
    result = None
    deadline = time.time() + 4
    while time.time() < deadline:
        result = open_first_search_result(window, search_box)
        if result:
            break
        time.sleep(0.3)
    if result is not None:
        result.click_input()
        time.sleep(0.5)
        return window
    try:
        search_box.click_input()
        send_keys("{DOWN}{ENTER}")
        time.sleep(0.5)
        return window
    except Exception:
        pass
    raise ContactNotFoundError(name)


def wa_chrome_search_by_name(name):
    opened_new = ensure_session(whatsapp_web_session, "https://web.whatsapp.com")
    if opened_new:
        time.sleep(4)
    click_selector(whatsapp_web_session["ws_url"], "[data-icon='search'], [data-icon='chat-search']")
    time.sleep(0.3)
    type_text(whatsapp_web_session["ws_url"], name)
    time.sleep(1.2)
    click_selector(whatsapp_web_session["ws_url"], "[data-testid='cell-frame-container'], div[role='listitem']")
    time.sleep(0.5)


def wa_search_and_open(contact):
    if is_phone_number(contact):
        wa_open_chat(contact)
        time.sleep(1.5)
        return
    wa_native_search_and_open(contact)


@app.route("/whatsapp/open", methods=["POST"])
def wa_open():
    with wa_lock:
        was_running = wa_is_running()
        if not was_running:
            wa_launch()
        wa_get_window()
    return jsonify({"status": "ok", "message": "Opened WhatsApp Desktop" if not was_running else "WhatsApp already open"})


@app.route("/whatsapp/search", methods=["POST"])
def wa_search():
    data = request.get_json(force=True) or {}
    contact = (data.get("contact") or "").strip()
    if not contact:
        return jsonify({"status": "error", "message": "Missing 'contact'"}), 400
    mode = whatsapp_mode()
    try:
        with wa_lock:
            if mode == "native" or is_phone_number(contact):
                wa_search_and_open(contact)
            else:
                wa_chrome_search_by_name(contact)
    except ContactNotFoundError:
        return jsonify({"status": "not_found", "message": f"'{contact}' is not in your contacts"}), 200
    except Exception:
        return jsonify({"status": "error", "message": f"Something went wrong searching for '{contact}'"}), 500
    return jsonify({"status": "ok", "message": f"Opened chat with '{contact}'"})


@app.route("/whatsapp/send", methods=["POST"])
def wa_send():
    data = request.get_json(force=True) or {}
    contact = (data.get("contact") or "").strip()
    message = (data.get("message") or "").strip()
    if not contact or not message:
        return jsonify({"status": "error", "message": "Missing 'contact' or 'message'"}), 400
    if is_phone_number(contact):
        with wa_lock:
            wa_open_chat(contact, message)
            time.sleep(2)
            send_keys("{ENTER}")
        return jsonify({"status": "ok", "message": f"Message sent to {contact}"})
    mode = whatsapp_mode()
    try:
        with wa_lock:
            if mode == "native":
                wa_native_search_and_open(contact)
                time.sleep(1)
                send_keys(message, with_spaces=True)
                send_keys("{ENTER}")
            else:
                wa_chrome_search_by_name(contact)
                time.sleep(1)
                click_selector(whatsapp_web_session["ws_url"],
                    "[data-testid='conversation-compose-box-input'], div[contenteditable='true'][data-tab]")
                type_text(whatsapp_web_session["ws_url"], message)
                press_enter(whatsapp_web_session["ws_url"])
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not message '{contact}': {e}"}), 500
    return jsonify({"status": "ok", "message": f"Message sent to '{contact}'"})


@app.route("/whatsapp/send_file", methods=["POST"])
def wa_send_file():
    data = request.get_json(force=True) or {}
    contact = (data.get("contact") or "").strip()
    filename = (data.get("filename") or "").strip()
    caption = (data.get("message") or "").strip()
    if not contact or not filename:
        return jsonify({"status": "error", "message": "Missing 'contact' or 'filename'"}), 400
    file_path = resolve_filename(filename)
    if not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": f"File not found: {filename}"}), 404
    with wa_lock:
        window = wa_open_chat(contact)
        time.sleep(1.5)
        attach_btn = window.child_window(title="Attach", control_type="Button")
        attach_btn.click_input()
        time.sleep(0.5)
        doc_option = window.child_window(title_re=".*Document.*", control_type="MenuItem")
        doc_option.click_input()
        time.sleep(1)
        dialog = Application(backend="uia").connect(title_re="Open", timeout=10).window(title_re="Open")
        dialog.child_window(control_type="Edit").set_edit_text(file_path)
        dialog.child_window(title="Open", control_type="Button").click_input()
        time.sleep(2)
        if caption:
            send_keys(caption, with_spaces=True)
        send_keys("{ENTER}")
    return jsonify({"status": "ok", "message": f"Sent file to {contact}"})


@app.route("/whatsapp/close", methods=["POST"])
def wa_close():
    with wa_lock:
        if not wa_is_running():
            return jsonify({"status": "ok", "message": "WhatsApp was not open"})
        try:
            Application(backend="uia").connect(title_re=WHATSAPP_WINDOW_TITLE_RE, timeout=2).kill()
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to close: {e}"}), 500
    return jsonify({"status": "ok", "message": "Closed WhatsApp"})


# ===========================================================================
# INSTAGRAM
# ===========================================================================
ig_lock = threading.Lock()


def ig_ensure_chrome_session():
    return ensure_session(instagram_session, "https://www.instagram.com")


def ig_chrome_search(name):
    opened_new = ig_ensure_chrome_session()
    if opened_new:
        time.sleep(3)
    click_selector(instagram_session["ws_url"], "svg[aria-label='Search']")
    time.sleep(0.4)
    click_selector(instagram_session["ws_url"], "input[placeholder='Search'], input[aria-label='Search Input']")
    type_text(instagram_session["ws_url"], name)
    time.sleep(1.3)


def ig_chrome_open_first_result():
    click_selector(instagram_session["ws_url"], "a[role='link']")
    time.sleep(1.5)


def ig_chrome_send(name, message):
    ig_chrome_search(name)
    ig_chrome_open_first_result()
    click_selector(instagram_session["ws_url"], "svg[aria-label='Messenger']")
    time.sleep(1.5)
    click_selector(instagram_session["ws_url"], "textarea[placeholder^='Message'], div[contenteditable='true']")
    type_text(instagram_session["ws_url"], message)
    press_enter(instagram_session["ws_url"])


@app.route("/instagram/open", methods=["POST"])
def ig_open():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    try:
        with ig_lock:
            opened_new = ig_ensure_chrome_session()
            if query:
                ig_chrome_search(query)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    message = "Opened Instagram" + (f" and searched for '{query}'" if query else "")
    return jsonify({"status": "ok", "message": message})


@app.route("/instagram/search", methods=["POST"])
def ig_search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Missing 'query'"}), 400
    try:
        with ig_lock:
            ig_chrome_search(query)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "ok", "message": f"Searched Instagram for '{query}'"})


@app.route("/instagram/send", methods=["POST"])
def ig_send():
    data = request.get_json(force=True) or {}
    contact = (data.get("contact") or "").strip()
    message = (data.get("message") or "").strip()
    if not contact or not message:
        return jsonify({"status": "error", "message": "Missing 'contact' or 'message'"}), 400
    try:
        with ig_lock:
            if ig_ensure_chrome_session():
                time.sleep(3)
            ig_chrome_send(contact, message)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not message '{contact}': {e}"}), 500
    return jsonify({"status": "ok", "message": f"Message sent to {contact} on Instagram"})


@app.route("/instagram/close", methods=["POST"])
def ig_close():
    return jsonify({"status": "ok", "message": close_session(instagram_session, "Instagram")})


# ===========================================================================
# VS CODE
# ===========================================================================
@app.route("/vscode/open", methods=["POST"])
def vscode_open():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip() or None
    exe = find_installed_exe(VSCODE_EXE_CANDIDATES)
    try:
        if exe:
            subprocess.Popen([exe] + ([path] if path else []))
        else:
            subprocess.Popen(["code"] + ([path] if path else []), shell=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not launch VS Code: {e}"}), 500
    return jsonify({"status": "ok", "message": "Opened VS Code" + (f" at '{path}'" if path else "")})


@app.route("/vscode/close", methods=["POST"])
def vscode_close():
    try:
        Application(backend="uia").connect(title_re=VSCODE_WINDOW_TITLE_RE, timeout=2).kill()
    except Exception:
        return jsonify({"status": "ok", "message": "VS Code was not open"})
    return jsonify({"status": "ok", "message": "Closed VS Code"})


# ===========================================================================
# GOOGLE
# ===========================================================================
@app.route("/google/open", methods=["POST"])
def google_open():
    opened_new = ensure_session(google_session, "https://www.google.com")
    return jsonify({"status": "ok", "message": "Opened Google" if opened_new else "Google already open"})


@app.route("/google/search", methods=["POST"])
def google_search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Missing 'query'"}), 400
    ensure_session(google_session, "https://www.google.com")
    encoded = requests.utils.quote(query)
    navigate(google_session["ws_url"], f"https://www.google.com/search?q={encoded}")
    time.sleep(1.2)
    return jsonify({"status": "ok", "message": f"Searched Google for '{query}'"})


@app.route("/google/close", methods=["POST"])
def google_close():
    return jsonify({"status": "ok", "message": close_session(google_session, "Google")})


# ===========================================================================
# TERMINAL
# ===========================================================================
@app.route("/terminal/open", methods=["POST"])
def terminal_open():
    try:
        try:
            subprocess.Popen(["wt.exe"])
        except FileNotFoundError:
            subprocess.Popen(["cmd.exe"])
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not launch terminal: {e}"}), 500
    time.sleep(1)
    return jsonify({"status": "ok", "message": "Opened terminal"})


@app.route("/terminal/search", methods=["POST"])
def terminal_search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Missing 'query'"}), 400
    try:
        window = get_native_window(".*Windows Terminal.*", timeout=5)
        send_keys("^+f")
        time.sleep(0.3)
        send_keys(query, with_spaces=True)
        send_keys("{ENTER}")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not search terminal: {e}"}), 409
    return jsonify({"status": "ok", "message": f"Searched terminal for '{query}'"})


@app.route("/terminal/close", methods=["POST"])
def terminal_close():
    try:
        Application(backend="uia").connect(title_re=TERMINAL_WINDOW_TITLE_RE, timeout=2).kill()
    except Exception:
        return jsonify({"status": "ok", "message": "Terminal was not open"})
    return jsonify({"status": "ok", "message": "Closed terminal"})


# ===========================================================================
# FILE MANAGER
# ===========================================================================
@app.route("/filemanager/open", methods=["POST"])
def fm_open():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip() or os.path.expanduser("~")
    try:
        subprocess.Popen(["explorer.exe", path])
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not open File Explorer: {e}"}), 500
    time.sleep(1)
    return jsonify({"status": "ok", "message": f"Opened File Explorer at '{path}'"})



@app.route("/filemanager/search", methods=["POST"])
def fm_search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    path = (data.get("path") or "").strip() or os.path.expanduser("~")
    if not query:
        return jsonify({"status": "error", "message": "Missing 'query'"}), 400
    try:
        desktop = Desktop(backend="uia")

        # snapshot existing Explorer window handles before opening a new one
        before = {
            w.handle
            for w in desktop.windows(title_re=FILE_EXPLORER_WINDOW_TITLE_RE, visible_only=True)
        }

        subprocess.Popen(["explorer.exe", path])

        # poll for a new window handle that wasn't there before
        target = None
        deadline = time.time() + 5
        while time.time() < deadline:
            current = desktop.windows(title_re=FILE_EXPLORER_WINDOW_TITLE_RE, visible_only=True)
            new_windows = [w for w in current if w.handle not in before]
            if new_windows:
                target = new_windows[-1]  # most recently appeared
                break
            time.sleep(0.2)

        if target is None:
            return jsonify({"status": "error", "message": "New File Explorer window did not appear"}), 500

        target.set_focus()
        time.sleep(0.3)
        send_keys("^e")
        time.sleep(0.3)
        send_keys(query, with_spaces=True)
        send_keys("{ENTER}")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Search failed: {e}"}), 500
    return jsonify({"status": "ok", "message": f"Searched File Explorer for '{query}'"})


@app.route("/filemanager/close", methods=["POST"])
def fm_close():
    try:
        Application(backend="uia").connect(title_re=FILE_EXPLORER_WINDOW_TITLE_RE, timeout=2).kill()
    except Exception:
        return jsonify({"status": "ok", "message": "File Explorer was not open"})
    return jsonify({"status": "ok", "message": "Closed File Explorer"})


# ===========================================================================
# STATUS
# ===========================================================================
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "youtube":     {"active": session_alive(youtube_session), "last_search": youtube_session["last_search"]},
        "whatsapp":    {"active": wa_is_running(), "mode": whatsapp_mode()},
        "instagram":   {"active": session_alive(instagram_session)},
        "vscode":      {"active": native_window_exists(VSCODE_WINDOW_TITLE_RE)},
        "google":      {"active": session_alive(google_session)},
        "terminal":    {"active": native_window_exists(TERMINAL_WINDOW_TITLE_RE)},
        "filemanager": {"active": native_window_exists(FILE_EXPLORER_WINDOW_TITLE_RE)},
        "orb":         {"mode": current_orb_state["mode"]},
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)