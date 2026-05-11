"""
modules/listener.py
Speech-to-Text module.
- Primary (offline): Vosk (fast, fully offline, no internet)
- Fallback:          SpeechRecognition with Google STT (needs internet)

Install:
    pip install SpeechRecognition vosk pyaudio
    Download a Vosk model from https://alphacephei.com/vosk/models
    e.g. vosk-model-small-en-us-0.15  (40 MB, fast)
    Place the extracted folder at: nova/models/vosk-model/
"""

import speech_recognition as sr
import os

VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "vosk-model")

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8   # seconds of silence before stopping
        self.recognizer.energy_threshold = 300  # mic sensitivity (raise if noisy room)
        self.mic = sr.Microphone()

        # Try loading Vosk for offline recognition
        self.vosk_model = None
        self._load_vosk()

        # Calibrate mic to ambient noise once at startup
        print("[Listener] Calibrating microphone...")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Listener] Ready.")

    def _load_vosk(self):
        """Load Vosk offline STT model if available."""
        try:
            from vosk import Model, KaldiRecognizer  # noqa
            if os.path.isdir(VOSK_MODEL_PATH):
                self.vosk_model = VOSK_MODEL_PATH
                print(f"[Listener] Vosk model loaded from {VOSK_MODEL_PATH}")
            else:
                print(f"[Listener] Vosk model not found at {VOSK_MODEL_PATH}.")
                print("[Listener] Falling back to Google STT (requires internet).")
        except ImportError:
            print("[Listener] Vosk not installed. Using Google STT (requires internet).")

    def listen(self, timeout=5, phrase_limit=10):
        """
        Listen from mic and return recognised text, or None on failure.
        timeout     : seconds to wait for speech to start
        phrase_limit: max seconds of speech to capture
        """
        with self.mic as source:
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
            except sr.WaitTimeoutError:
                return None

        # --- Offline path: Vosk ---
        if self.vosk_model:
            try:
                text = self.recognizer.recognize_vosk(audio, model=self.vosk_model)
                import json
                result = json.loads(text)
                return result.get("text", "").strip() or None
            except Exception as e:
                print(f"[Listener] Vosk error: {e}. Trying Google STT...")

        # --- Online fallback: Google STT ---
        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            print("[Listener] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[Listener] Google STT request failed: {e}")
            return None
