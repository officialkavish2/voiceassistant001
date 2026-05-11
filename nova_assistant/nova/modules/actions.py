"""
modules/actions.py
Executes real PC actions: open apps, search, screenshot, volume, etc.
Works on Windows, Linux, and macOS.
"""

import os
import sys
import subprocess
import platform
import datetime
import webbrowser
import urllib.parse

OS = platform.system()  # "Windows" | "Linux" | "Darwin"

class Actions:
    def execute(self, action_key: str, data: dict) -> str | None:
        """
        Route action_key to the correct handler.
        Returns a spoken response string, or None to use the brain's response.
        """
        handlers = {
            "open_app":   self.open_app,
            "web_search": self.web_search,
            "youtube":    self.youtube,
            "volume":     self.volume_control,
            "screenshot": self.screenshot,
            "lock_screen":self.lock_screen,
            "shutdown":   self.shutdown,
            "restart":    self.restart,
            "sleep":      self.sleep,
        }
        handler = handlers.get(action_key)
        if handler:
            try:
                return handler(data)
            except Exception as e:
                print(f"[Actions] Error in '{action_key}': {e}")
                return f"Sorry, I couldn't complete that action: {e}"
        print(f"[Actions] Unknown action: {action_key}")
        return None

    # ── App Launcher ────────────────────────────────────────────────
    def open_app(self, data: dict) -> str | None:
        app = data.get("app", "")
        if not app:
            return "I didn't catch which app to open."

        if OS == "Windows":
            # Windows app aliases
            win_apps = {
                "chrome":     "start chrome",
                "firefox":    "start firefox",
                "notepad":    "notepad",
                "calculator": "calc",
                "explorer":   "explorer",
                "code":       "code",
                "terminal":   "start cmd",
                "winword":    "start winword",
                "excel":      "start excel",
                "spotify":    "start spotify",
            }
            cmd = win_apps.get(app, f"start {app}")
            subprocess.Popen(cmd, shell=True)

        elif OS == "Linux":
            linux_apps = {
                "chrome":     "google-chrome",
                "firefox":    "firefox",
                "terminal":   "gnome-terminal",
                "notepad":    "gedit",
                "calculator": "gnome-calculator",
                "nautilus":   "nautilus",
                "code":       "code",
                "vlc":        "vlc",
                "spotify":    "spotify",
            }
            cmd = linux_apps.get(app, app)
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        elif OS == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app])

        return None  # Use brain's response text

    # ── Web Search ──────────────────────────────────────────────────
    def web_search(self, data: dict) -> str | None:
        query = data.get("query", "")
        if not query:
            return "What would you like me to search for?"
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return None

    # ── YouTube ─────────────────────────────────────────────────────
    def youtube(self, data: dict) -> str | None:
        query = data.get("query", "")
        url = ("https://www.youtube.com/results?search_query="
               + urllib.parse.quote(query))
        webbrowser.open(url)
        return None

    # ── Volume Control ──────────────────────────────────────────────
    def volume_control(self, data: dict) -> str | None:
        direction = data.get("direction", "")

        if OS == "Windows":
            # Uses nircmd (optional) or keyboard shortcuts
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_APPCOMMAND = 0x0319
                commands = {
                    "up":   0x0A0000,
                    "down": 0x090000,
                    "mute": 0x080000,
                }
                if direction in commands:
                    ctypes.windll.user32.SendMessageW(
                        HWND_BROADCAST, WM_APPCOMMAND, 0, commands[direction])
            except Exception as e:
                print(f"[Actions] Volume error: {e}")

        elif OS == "Linux":
            cmds = {
                "up":   ["amixer", "-q", "sset", "Master", "5%+"],
                "down": ["amixer", "-q", "sset", "Master", "5%-"],
                "mute": ["amixer", "-q", "sset", "Master", "toggle"],
            }
            if direction in cmds:
                subprocess.run(cmds[direction])

        elif OS == "Darwin":
            scripts = {
                "up":   'set volume output volume (output volume of (get volume settings) + 10)',
                "down": 'set volume output volume (output volume of (get volume settings) - 10)',
                "mute": 'set volume with output muted',
            }
            if direction in scripts:
                subprocess.run(["osascript", "-e", scripts[direction]])

        return None

    # ── Screenshot ──────────────────────────────────────────────────
    def screenshot(self, data: dict) -> str:
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = os.path.join(os.path.expanduser("~"),
                                     f"screenshot_{timestamp}.png")
            img = pyautogui.screenshot()
            img.save(filename)
            return f"Screenshot saved to your home folder as screenshot_{timestamp}.png"
        except ImportError:
            return "Screenshot feature requires pyautogui. Run: pip install pyautogui"
        except Exception as e:
            return f"Screenshot failed: {e}"

    # ── Lock Screen ─────────────────────────────────────────────────
    def lock_screen(self, data: dict) -> str | None:
        if OS == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif OS == "Linux":
            for cmd in [["gnome-screensaver-command", "--lock"],
                        ["xdg-screensaver", "lock"],
                        ["loginctl", "lock-session"]]:
                try:
                    subprocess.run(cmd)
                    break
                except FileNotFoundError:
                    continue
        elif OS == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"])
        return None

    # ── Power Actions ────────────────────────────────────────────────
    def shutdown(self, data: dict) -> str | None:
        if OS == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "5"])
        else:
            subprocess.run(["shutdown", "-h", "+0"])
        return "Shutting down in 5 seconds."

    def restart(self, data: dict) -> str | None:
        if OS == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "5"])
        else:
            subprocess.run(["shutdown", "-r", "+0"])
        return "Restarting in 5 seconds."

    def sleep(self, data: dict) -> str | None:
        if OS == "Windows":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        elif OS == "Linux":
            subprocess.run(["systemctl", "suspend"])
        elif OS == "Darwin":
            subprocess.run(["pmset", "sleepnow"])
        return None
