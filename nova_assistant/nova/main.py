"""
Nova - Offline Jarvis-style Personal Assistant
Run: python main.py
"""

import time
from modules.listener   import Listener
from modules.speaker    import Speaker
from modules.brain      import Brain
from modules.actions    import Actions

WAKE_WORD = "nova"

def main():
    print("=" * 50)
    print("  NOVA - Offline Personal Assistant")
    print("  Say 'Nova' to wake me up")
    print("  Say 'Nova exit' to quit")
    print("=" * 50)

    listener = Listener()
    speaker  = Speaker()
    brain    = Brain()
    actions  = Actions()

    speaker.speak("Nova is online. Say Nova to activate me.")

    while True:
        try:
            # Always listening for wake word
            print("\n[Listening for wake word...]")
            audio_text = listener.listen(timeout=5)

            if not audio_text:
                continue

            audio_text = audio_text.lower().strip()
            print(f"[Heard]: {audio_text}")

            # Wake word check
            if WAKE_WORD not in audio_text:
                continue

            # Strip wake word, get the actual command
            command = audio_text.replace(WAKE_WORD, "").strip()

            # Exit command
            if command in ("exit", "quit", "bye", "goodbye", "shutdown"):
                speaker.speak("Goodbye! Nova shutting down.")
                break

            # Empty command after wake word — prompt for input
            if not command:
                speaker.speak("Yes? How can I help?")
                print("[Listening for command...]")
                command = listener.listen(timeout=6)
                if not command:
                    speaker.speak("I didn't catch that. Please try again.")
                    continue
                command = command.lower().strip()
                print(f"[Command]: {command}")

            # Brain decides what to do
            response, action_key, action_data = brain.process(command)

            # Execute action if needed
            if action_key:
                action_result = actions.execute(action_key, action_data)
                if action_result:
                    response = action_result

            # Speak and print the response
            print(f"[Nova]: {response}")
            speaker.speak(response)

        except KeyboardInterrupt:
            print("\nStopped by user.")
            speaker.speak("Nova stopped.")
            break
        except Exception as e:
            print(f"[Error]: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
