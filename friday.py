import requests
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
import subprocess
import sys
import os
import time


# ============================================================
# INITIALIZATION
# ============================================================

pygame.mixer.init()

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8


# ============================================================
# SETTINGS
# ============================================================

WEBHOOK_URL = "http://localhost:5678/webhook/friday"
ORB_URL = "http://localhost:5000/set"

SESSION_ID = "friday-main-session"

active = False


# ============================================================
# VOICES
# ============================================================

VOICES = {
    "en": "en-US-AriaNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural",
}


# ============================================================
# ORB WINDOW
# ============================================================

def launch_orb_window():

    try:

        orb_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "OrbWindow.py"
        )

        subprocess.Popen([
            sys.executable,
            orb_path
        ])

        print("Orb window started.")

    except Exception as e:

        print("Orb window failed to launch:", e)


def set_orb(mode):

    try:

        requests.post(
            f"{ORB_URL}/{mode}",
            timeout=0.5
        )

    except Exception:

        pass


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_voice(text):

    for ch in text:

        code = ord(ch)

        # Telugu
        if 0x0C00 <= code <= 0x0C7F:
            return "te"

        # Hindi / Devanagari
        if 0x0900 <= code <= 0x097F:
            return "hi"

        # Tamil
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"

        # Kannada
        if 0x0C80 <= code <= 0x0CFF:
            return "kn"

        # Malayalam
        if 0x0D00 <= code <= 0x0D7F:
            return "ml"

    return "en"


# ============================================================
# TEXT TO SPEECH
# ============================================================

async def _speak(text):

    if not text:
        return

    try:

        set_orb("responding")

        language = detect_voice(text)

        voice = VOICES.get(
            language,
            VOICES["en"]
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+10%",
            pitch="+2Hz"
        )

        filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "voice.mp3"
        )

        await communicate.save(filename)

        pygame.mixer.music.load(filename)

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():

            await asyncio.sleep(0.1)

        pygame.mixer.music.unload()

        set_orb("idle")

    except Exception as e:

        set_orb("idle")

        print("TTS Error:", e)


def speak(text):

    try:

        asyncio.run(
            _speak(text)
        )

    except Exception as e:

        print("Speech error:", e)


# ============================================================
# MICROPHONE LISTENING
# ============================================================

def listen():

    set_orb("listening")

    try:

        with sr.Microphone() as source:

            print("\nListening...")

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

        text = recognizer.recognize_google(
            audio
        )

        text = text.lower().strip()

        print("You :", text)

        set_orb("idle")

        return text

    except Exception:

        set_orb("idle")

        raise


# ============================================================
# CONNECT TO N8N
# ============================================================

def send_to_n8n(text):

    payload = {
        "text": text,
        "session_id": SESSION_ID
    }

    try:

        print("\nSending to n8n...")

        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        print("Reply    :", data.get("reply"))
        print("Language :", data.get("language"))

        return data

    except requests.exceptions.RequestException as e:

        print("n8n Connection Error:", e)

        return None

    except ValueError:

        print("Invalid JSON received from n8n")

        return None


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_text(command):

    global active

    command = command.lower().strip()


    # --------------------------------------------------------
    # GOODBYE = SLEEP
    # --------------------------------------------------------

    if any(x in command for x in [
        "goodbye",
        "good bye",
        "go to sleep",
        "sleep friday",
        "sleep"
    ]):

        active = False

        speak(
            "Going to sleep, boss. "
            "Call me whenever you need me."
        )

        return True


    # --------------------------------------------------------
    # SEND COMMAND TO N8N
    # --------------------------------------------------------

    data = send_to_n8n(command)

    if data:

        reply = data.get(
            "reply",
            "Sorry boss."
        )

        speak(reply)

    else:

        speak(
            "Sorry boss, "
            "I couldn't connect to the AI service."
        )

    return True


# ============================================================
# MAIN FRIDAY LOOP
# ============================================================

def run_friday():

    global active


    # --------------------------------------------------------
    # START ORB
    # --------------------------------------------------------

    launch_orb_window()

    time.sleep(2)


    # --------------------------------------------------------
    # START MESSAGE
    # --------------------------------------------------------

    speak(
        "Friday systems online. "
        "Awaiting your command, boss."
    )


    active = False


    # ========================================================
    # CONTINUOUS LOOP
    # ========================================================

    while True:

        try:


            # ==================================================
            # SLEEP MODE
            # ==================================================

            if not active:

                print(
                    "\n💤 Friday is sleeping."
                    " Say 'Friday' to wake me."
                )

                set_orb("idle")


                try:

                    text = listen()

                except sr.WaitTimeoutError:

                    continue


                # ----------------------------------------------
                # WAKE WORD
                # ----------------------------------------------

                if "friday" in text:

                    active = True

                    speak(
                        "Yes boss."
                    )

                continue


            # ==================================================
            # ACTIVE MODE
            # ==================================================

            print(
                "\n🟢 Friday is active."
                " Listening for command..."
            )


            try:

                command = listen()

            except sr.WaitTimeoutError:

                continue


            if not command:

                continue


            command = command.lower().strip()


            # ==================================================
            # SHUTDOWN FRIDAY
            # ==================================================

            if any(x in command for x in [
                "shutdown friday",
                "shut down friday",
                "exit friday",
                "quit friday",
                "close friday"
            ]):

                speak(
                    "Shutting down Friday. "
                    "Goodbye boss."
                )

                break


            # ==================================================
            # GOODBYE = SLEEP
            # ==================================================

            if any(x in command for x in [
                "goodbye",
                "good bye",
                "go to sleep",
                "sleep friday"
            ]):

                active = False

                speak(
                    "Going to sleep, boss. "
                    "Call me whenever you need me."
                )

                continue


            # ==================================================
            # NORMAL COMMAND
            # ==================================================

            process_text(command)


        # ======================================================
        # SPEECH NOT UNDERSTOOD
        # ======================================================

        except sr.UnknownValueError:

            set_orb("idle")

            print(
                "Didn't understand."
            )


        # ======================================================
        # LISTENING TIMEOUT
        # ======================================================

        except sr.WaitTimeoutError:

            set_orb("idle")

            continue


        # ======================================================
        # CTRL + C
        # ======================================================

        except KeyboardInterrupt:

            print(
                "\nFriday interrupted."
            )

            try:

                speak(
                    "Shutting down. "
                    "Goodbye boss."
                )

            except Exception:

                pass

            break


        # ======================================================
        # OTHER ERRORS
        # ======================================================

        except Exception as e:

            set_orb("idle")

            print(
                "Error:",
                e
            )


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    run_friday()