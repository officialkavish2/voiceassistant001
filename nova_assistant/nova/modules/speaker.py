"""
modules/speaker.py
Text-to-Speech module.
- Primary (offline): pyttsx3  (uses OS built-in voices, zero latency)
- Optional upgrade:  Coqui-TTS (better quality, still offline, slower)

Install:
    pip install pyttsx3
    Optional: pip install TTS  (Coqui-TTS, large download ~500 MB)
"""

import pyttsx3
import threading

class Speaker:
    def __init__(self, rate=175, volume=1.0, voice_index=0):
        """
        rate        : speech speed (words per minute). Default 175.
        volume      : 0.0 to 1.0
        voice_index : 0 = first available voice (usually male),
                      1 = second voice (often female)
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate",   rate)
        self.engine.setProperty("volume", volume)

        # Pick voice
        voices = self.engine.getProperty("voices")
        if voices and voice_index < len(voices):
            self.engine.setProperty("voice", voices[voice_index].id)
            print(f"[Speaker] Using voice: {voices[voice_index].name}")
        else:
            print("[Speaker] Default voice selected.")

        self._lock = threading.Lock()

    def speak(self, text: str):
        """Convert text to speech (blocking call)."""
        if not text:
            return
        print(f"[Speaking]: {text}")
        with self._lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def speak_async(self, text: str):
        """Non-blocking speak — fire and forget."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def list_voices(self):
        """Print all available voices — useful for setup."""
        voices = self.engine.getProperty("voices")
        for i, v in enumerate(voices):
            print(f"  [{i}] {v.name} | {v.id}")
