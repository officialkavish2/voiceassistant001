"""
modules/brain.py
Natural Language Understanding — decides what Nova should do.

Two modes:
  1. Rule-based  : fast keyword matching, works with zero extra installs
  2. LLM-powered : passes command to local Ollama for flexible understanding
                   (requires Ollama running: https://ollama.com)

The brain returns a tuple: (response_text, action_key, action_data)
  response_text : what Nova says
  action_key    : string key for the Actions module (or None)
  action_data   : dict of extra data for the action (or {})
"""

import datetime
import random

# Optional Ollama integration (offline LLM)
try:
    import ollama as _ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

OLLAMA_MODEL = "llama3.2"  # Change to any model you have pulled

SYSTEM_PROMPT = """You are Nova, a helpful offline voice assistant on the user's PC.
Be concise — your replies will be spoken aloud, so keep them under 2 sentences.
If the user wants to open an app, control the system, or automate something,
reply with a short confirmation. Never use markdown or bullet points."""

class Brain:
    def __init__(self, use_llm=True):
        self.use_llm = use_llm and OLLAMA_AVAILABLE
        if self.use_llm:
            print(f"[Brain] LLM mode ON — using Ollama model '{OLLAMA_MODEL}'")
        else:
            print("[Brain] Rule-based mode (Ollama not available or disabled)")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def process(self, command: str):
        """
        Returns: (response: str, action_key: str|None, action_data: dict)
        """
        command = command.lower().strip()

        # Always handle these with rules (fast, reliable)
        result = self._rule_based(command)
        if result:
            return result

        # Unknown command — try LLM or give a fallback response
        if self.use_llm:
            response = self._ask_llm(command)
            return response, None, {}

        return "I'm not sure how to help with that yet.", None, {}

    # ------------------------------------------------------------------
    # Rule-based intent matching
    # ------------------------------------------------------------------
    def _rule_based(self, cmd):
        # ── Time & Date ──────────────────────────────────────────────
        if any(w in cmd for w in ("time", "what time")):
            now = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}.", None, {}

        if any(w in cmd for w in ("date", "today", "what day")):
            today = datetime.datetime.now().strftime("%A, %B %d %Y")
            return f"Today is {today}.", None, {}

        # ── Greetings ─────────────────────────────────────────────────
        if any(w in cmd for w in ("hello", "hi", "hey", "good morning",
                                   "good evening", "good afternoon")):
            greetings = [
                "Hello! How can I help you?",
                "Hi there! What do you need?",
                "Hey! I'm here. What's up?"
            ]
            return random.choice(greetings), None, {}

        # ── Open Applications ─────────────────────────────────────────
        app_map = {
            "chrome":      "chrome",
            "firefox":     "firefox",
            "browser":     "chrome",
            "notepad":     "notepad",
            "calculator":  "calculator",
            "vs code":     "code",
            "vscode":      "code",
            "terminal":    "terminal",
            "file manager":"nautilus",   # Linux; "explorer" on Windows
            "explorer":    "explorer",
            "spotify":     "spotify",
            "vlc":         "vlc",
            "word":        "winword",
            "excel":       "excel",
        }
        if cmd.startswith("open ") or "launch " in cmd:
            for keyword, app in app_map.items():
                if keyword in cmd:
                    return f"Opening {keyword}.", "open_app", {"app": app}
            # Generic — try to open whatever they said
            app_name = cmd.replace("open ", "").replace("launch ", "").strip()
            return f"Trying to open {app_name}.", "open_app", {"app": app_name}

        # ── Web Search ────────────────────────────────────────────────
        if "search" in cmd or "google" in cmd or "look up" in cmd:
            query = (cmd.replace("search for", "")
                       .replace("search", "")
                       .replace("google", "")
                       .replace("look up", "")
                       .strip())
            if query:
                return f"Searching for {query}.", "web_search", {"query": query}

        # ── YouTube ───────────────────────────────────────────────────
        if "youtube" in cmd or "play on youtube" in cmd:
            query = (cmd.replace("play on youtube", "")
                       .replace("youtube", "")
                       .replace("play", "")
                       .strip())
            return f"Playing {query} on YouTube.", "youtube", {"query": query}

        # ── Volume ────────────────────────────────────────────────────
        if "volume up" in cmd or "increase volume" in cmd:
            return "Turning volume up.", "volume", {"direction": "up"}
        if "volume down" in cmd or "decrease volume" in cmd:
            return "Turning volume down.", "volume", {"direction": "down"}
        if "mute" in cmd:
            return "Muting audio.", "volume", {"direction": "mute"}

        # ── System ────────────────────────────────────────────────────
        if "screenshot" in cmd:
            return "Taking a screenshot.", "screenshot", {}

        if "lock" in cmd and "screen" in cmd:
            return "Locking your screen.", "lock_screen", {}

        if any(w in cmd for w in ("shut down", "shutdown", "power off")):
            return "Shutting down the computer.", "shutdown", {}

        if "restart" in cmd or "reboot" in cmd:
            return "Restarting the computer.", "restart", {}

        if "sleep" in cmd:
            return "Putting the computer to sleep.", "sleep", {}

        # ── Jokes ─────────────────────────────────────────────────────
        if "joke" in cmd or "make me laugh" in cmd:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
                "Why was the math book sad? It had too many problems.",
            ]
            return random.choice(jokes), None, {}

        # ── How are you ───────────────────────────────────────────────
        if "how are you" in cmd or "how do you feel" in cmd:
            return "I'm running perfectly, fully offline and at your service!", None, {}

        # ── What can you do ───────────────────────────────────────────
        if "what can you do" in cmd or "help" in cmd:
            return ("I can open apps, search the web, play YouTube, control volume, "
                    "take screenshots, tell the time and date, and more. "
                    "Just say Nova and your command."), None, {}

        return None  # No rule matched → fall through to LLM

    # ------------------------------------------------------------------
    # LLM fallback via Ollama (fully offline)
    # ------------------------------------------------------------------
    def _ask_llm(self, command: str) -> str:
        try:
            response = _ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": command}
                ]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"[Brain] Ollama error: {e}")
            return "Sorry, I couldn't process that request right now."
