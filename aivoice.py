import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import webbrowser
import pyttsx3
import subprocess

# ---------- VOSK (VOICE) ----------
import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# ---------- TEXT TO SPEECH ----------
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------- VOSK SETUP ----------
q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(bytes(indata))

model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

def listen_voice():
    speak("Listening")
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                return result.get("text", "").lower()

# ---------- OLLAMA AI ----------
def ask_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except Exception as e:
        return f"AI error: {e}"

# ---------- SMART OPEN DETECTION ----------
def detect_open_intent(text):
    sites = {
        "youtube": "https://www.youtube.com",
        "utube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "spotify": "https://open.spotify.com"
    }

    if "open" in text:
        for key, url in sites.items():
            if key in text:
                return url
    return None

# ---------- CHAT UI ----------
def create_chat_bubble(sender, message):
    bubble = tk.Frame(
        chat_area,
        bg="#DCF8C6" if sender.startswith("You") else "#E6E6E6",
        pady=5,
        padx=10
    )
    tk.Label(
        bubble,
        text=message,
        bg=bubble["bg"],
        font=("Arial", 12),
        wraplength=400,
        justify="left"
    ).pack(anchor="w")

    timestamp = datetime.now().strftime("%H:%M")
    tk.Label(
        bubble,
        text=f"{sender} • {timestamp}",
        bg=bubble["bg"],
        font=("Arial", 8),
        fg="gray"
    ).pack(anchor="e")

    chat_area.window_create(tk.END, window=bubble)
    chat_area.insert(tk.END, "\n\n")
    chat_area.yview(tk.END)

# ---------- TEXT INPUT ----------
def send_message():
    user_input = input_field.get().strip()
    if not user_input:
        return

    create_chat_bubble("You", user_input)
    input_field.delete(0, tk.END)

    # Time (real)
    if "time" in user_input.lower():
        now = datetime.now().strftime("%I:%M %p")
        speak(f"It is {now}")
        create_chat_bubble("Alfred", f"It is {now}")
        return

    # Open websites
    url = detect_open_intent(user_input.lower())
    if url:
        webbrowser.open(url)
        speak("Opening now")
        create_chat_bubble("Alfred", f"Opening {url}")
        return

    # AI chat
    response = ask_ollama(user_input)
    speak(response)
    create_chat_bubble("Alfred", response)

# ---------- VOICE INPUT ----------
def listen_and_send():
    user_input = listen_voice()
    if not user_input:
        return

    create_chat_bubble("You (voice)", user_input)

    url = detect_open_intent(user_input)
    if url:
        webbrowser.open(url)
        speak("Opening now")
        create_chat_bubble("Alfred", f"Opening {url}")
        return

    response = ask_ollama(user_input)
    speak(response)
    create_chat_bubble("Alfred", response)

# ---------- GUI ----------
root = tk.Tk()
root.title("Alfred – Offline AI Assistant 🤖")
root.geometry("500x600")
root.configure(bg="#ECE5DD")

chat_area = scrolledtext.ScrolledText(
    root,
    width=60,
    height=25,
    font=("Arial", 12),
    bg="#ECE5DD",
    bd=0
)
chat_area.pack(padx=10, pady=10)

input_frame = tk.Frame(root, bg="#ECE5DD")
input_frame.pack(pady=5)

input_field = tk.Entry(input_frame, width=30, font=("Arial", 14))
input_field.pack(side=tk.LEFT, padx=5)

send_button = tk.Button(
    input_frame,
    text="Send",
    command=send_message,
    font=("Arial", 12),
    bg="#128C7E",
    fg="white"
)
send_button.pack(side=tk.LEFT, padx=5)

listen_button = tk.Button(
    input_frame,
    text="🎤 Listen",
    command=listen_and_send,
    font=("Arial", 12),
    bg="#25D366",
    fg="white"
)
listen_button.pack(side=tk.LEFT)

speak("Hello! I'm Alfred. Running completely offline.")
root.mainloop()
