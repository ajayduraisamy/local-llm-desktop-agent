import requests
import speech_recognition as sr
import pyttsx3
import json
import re
import shutil


# ================= CONFIG =================

OLLAMA_URL = "http://localhost:11434/api/generate"
TOOLS_URL = "http://127.0.0.1:3333"

MODEL = "llama3:8b"

# =========================================


# ================= VOICE ==================

engine = pyttsx3.init()


def speak(text):
    print("Agent:", text)
    engine.say(text)
    engine.runAndWait()


# =========================================


# ================== LLM ===================

def ask_llm(user_text):

    prompt = f"""
SYSTEM:
You are an AI desktop automation agent.

You can control Windows apps and browser.

Available tools:

open(name)        -> Open application
open_url(name)    -> Open website
create(path)      -> Create file/folder
write(path,content)-> Write/Edit file
run(cmd)          -> Run system command

Rules:
- Never use delete
- Reply ONLY JSON
- No explanation
- No markdown

FORMAT:

{{
 "tool":"open|open_url|type|create|write|run|none",

 "args":{{}}
}}

If chat:

{{
 "tool":"none",
 "args":{{"text":"reply"}}
}}

User: {user_text}

Return JSON only:
"""

    res = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0,
            "top_p": 0.1
        },
        timeout=120
    )

    return res.json()["response"]


# =========================================


# ============== JSON EXTRACT ==============

def extract_json(text):

    match = re.search(r"\{.*\}", text, re.S)

    if not match:
        return None

    return match.group()

def call_tool(text):

    try:

        raw = extract_json(text)

        # If no JSON -> chat
        if not raw:
            return {"status": "ok", "msg": text.strip()}

        data = json.loads(raw)

        tool = data.get("tool", "none")
        args = data.get("args", {})

        # ---------- CHAT ----------

        if tool == "none":
            return {"status": "ok", "msg": args.get("text", "")}

        # ---------- SAFETY ----------

        if tool == "delete":
            return {"status": "ok", "msg": "Delete disabled"}

        # ---------- TYPE ----------

        if tool == "type":

            text_to_type = (
                args.get("text")
                or args.get("content")
                or ""
            )

            r = requests.post(
                f"{TOOLS_URL}/type",
                json={"content": text_to_type},
                timeout=30
            )

            return r.json()

        # ---------- OPEN URL ----------

        if tool == "open_url":

            url = (
                args.get("name")
                or args.get("url")
                or args.get("link")
                or ""
            )

            if not url:
                return {"status": "ok", "msg": "No URL found"}

            r = requests.post(
                f"{TOOLS_URL}/open_url",
                json={"name": url},
                timeout=30
            )

            return r.json()

        # ---------- OPEN APP ----------

        if tool == "open":

            name = (
                args.get("name")
                or args.get("program")
                or args.get("app")
                or ""
            )

            if not name:
                return {"status": "ok", "msg": "No app name found"}

            clean = name.lower().replace(" ", "")

            if not shutil.which(clean):

                return {
                    "status": "ok",
                    "msg": f"I cannot find {name}"
                }

            r = requests.post(
                f"{TOOLS_URL}/open",
                json={"name": name},
                timeout=30
            )

            return r.json()

        # ---------- OTHER TOOLS ----------

        r = requests.post(
            f"{TOOLS_URL}/{tool}",
            json=args,
            timeout=60
        )

        return r.json()

    except Exception as e:

        return {
            "status": "ok",
            "msg": text.strip()
        }

        # ---------------- OTHER TOOLS ----------------

        r = requests.post(
            f"{TOOLS_URL}/{tool}",
            json=args,
            timeout=60
        )

        return r.json()

    except Exception as e:

        # Fallback
        return {
            "status": "ok",
            "msg": text.strip()
        }


# =========================================


# =============== SPEECH ===================

def listen():

    r = sr.Recognizer()

    with sr.Microphone() as source:

        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)

        audio = r.listen(source)

    return r.recognize_google(audio)


# =========================================


# ================= MAIN ===================

def main():

    speak("Multimodal AI agent ready")

    while True:

        try:

            text = listen()

            print("You:", text)

            ai_out = ask_llm(text)

            print("AI RAW:", ai_out)

            result = call_tool(ai_out)

            print("Result:", result)

            speak(result.get("msg", "Done"))

        except KeyboardInterrupt:

            speak("Goodbye")
            break

        except Exception as e:

            print("Error:", e)
            speak("Something went wrong")


# =========================================


if __name__ == "__main__":
    main()
