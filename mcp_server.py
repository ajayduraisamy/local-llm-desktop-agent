from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import os
import pyautogui
import time

app = FastAPI(title="Ajay AI Tool Server")


# ---------- Models ----------

class OpenApp(BaseModel):
    name: str


class FileData(BaseModel):
    path: str
    content: str | None = None


class Command(BaseModel):
    cmd: str


# ---------- Tools ----------

@app.post("/open")
def open_app(data: OpenApp):
    subprocess.Popen(f"start {data.name}", shell=True)
    return {"status": "ok", "msg": f"{data.name} opened"}


@app.post("/create")
def create_file(data: FileData):

    # File
    if "." in data.path:
        open(data.path, "w").close()
        return {"status": "ok", "msg": "File created"}

    # Folder
    os.makedirs(data.path, exist_ok=True)
    return {"status": "ok", "msg": "Folder created"}


@app.post("/write")
def write_file(data: FileData):

    with open(data.path, "w", encoding="utf-8") as f:
        f.write(data.content or "")

    return {"status": "ok", "msg": "File updated"}

@app.post("/open_url")
def open_url(data: OpenApp):

    url = data.name

    if not url.startswith("http"):
        url = "https://" + url

    subprocess.Popen(f'start "" "{url}"', shell=True)

    return {"status": "ok", "msg": f"Opened {url}"}


@app.post("/run")
def run_cmd(data: Command):

    res = subprocess.run(
        data.cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    return {
        "status": "ok",
        "output": res.stdout + res.stderr
    }

@app.post("/type")
def type_text(data: FileData):

    time.sleep(2)  # Wait for focus

    pyautogui.write(data.content, interval=0.05)

    pyautogui.press("enter")

    return {"status": "ok", "msg": "Typed text"}




# ---------- Start Server ----------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=3333)
