import speech_recognition as sr
import pyttsx3
import subprocess
import os
import requests
import json

# ========== CONFIG ==========
BASE_DIR = os.getcwd()
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:8b"
# ============================

engine = pyttsx3.init()


def speak(text):
    print("Agent:", text)
    engine.say(text)
    engine.runAndWait()


r = sr.Recognizer()
mic = sr.Microphone()


def ask_ai(user_text):
    prompt = f"""
You are a Windows automation assistant.

Convert user request into JSON.

Rules:
1. Only return valid JSON.
2. No explanation.

Format:
{{
 "action":"create|write|run|open|delete|command|none",
 "path":"file_or_folder",
 "content":"optional",
 "cmd":"optional"
}}

User: {user_text}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return res.json()["response"]


def execute(data):
    try:
        data = json.loads(data)

        action = data.get("action")
        path = data.get("path", "")
        content = data.get("content", "")
        cmd = data.get("cmd", "")

        # CREATE FILE/FOLDER
        if action == "create":
            if "." in path:
                open(path, "w").close()
                speak(f"{path} created")
            else:
                os.makedirs(path, exist_ok=True)
                speak(f"Folder {path} created")

        # WRITE FILE
        elif action == "write":
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            speak(f"{path} updated")

        # RUN FILE
        elif action == "run":
            subprocess.Popen(f"python {path}", shell=True)
            speak("Program running")

        # OPEN APP/FOLDER
        elif action == "open":
            subprocess.Popen(path, shell=True)
            speak("Opened")

        # DELETE
        elif action == "delete":
            if os.path.isfile(path):
                os.remove(path)
            else:
                os.rmdir(path)
            speak("Deleted")

        # RAW COMMAND
        elif action == "command":
            subprocess.run(cmd, shell=True)
            speak("Done")

        else:
            speak("I didn't understand")

    except Exception as e:
        print("Error:", e)
        speak("Failed to execute")


def listen():
    with mic as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print("You:", text)
        return text
    except:
        return ""


def main():
    speak("Advanced voice agent ready")

    while True:
        text = listen()

        if text.lower() in ["exit", "stop", "quit"]:
            speak("Bye")
            break

        if text == "":
            continue

        ai_response = ask_ai(text)

        print("AI:", ai_response)

        execute(ai_response)


if __name__ == "__main__":
    main()
