# ---------- IMPORT ----------
import tkinter as tk
from tkinter import scrolledtext
from gpt4all import GPT4All
import threading
import requests
import time
import pygame
import json
from version import get_version

# ---------- VERSIONE ----------
VERSION = get_version()

# ---------- CONFIG MODELLO ----------
MODEL_FILE = r"C:\Users\campa\Desktop\progetto\qwen2.5-coder-7b-instruct-q4_0.gguf"

try:
    model = GPT4All(MODEL_FILE, allow_download=False)
except Exception as e:
    print("Errore caricamento modello:", e)
    exit()

model_lock = threading.Lock()

# ---------- MEMORIA ----------
chat_history = []
MESSAGGI_MAX_HISTORY = 20
stop_generation = False
barzellette_attive = True

# ---------- PROMPT ----------
system_prompt = (
    "sei un assistente utile. rispondi in minuscolo come sans di undertale. "
    "usa poche punteggiature e sii ironico."
)

# ---------- AUDIO ----------
pygame.mixer.init()

def play_sans_voice_loop():
    try:
        pygame.mixer.music.load("sans voice.mp3")
        pygame.mixer.music.play(-1)
    except:
        pass

def stop_sans_voice():
    pygame.mixer.music.stop()

# ---------- WIKIPEDIA ----------
def cerca_wikipedia(argomento):
    try:
        url = f"https://it.wikipedia.org/api/rest_v1/page/summary/{argomento.replace(' ','_')}"
        r = requests.get(url, timeout=5)

        if r.status_code == 200:
            data = r.json()
            return data.get("extract","nessuna informazione.")
        else:
            return "nessuna informazione trovata."

    except:
        return "errore wikipedia."

# ---------- SALVA MEMORIA ----------
def salva_chat():
    try:
        with open("chat_history.json","w",encoding="utf-8") as f:
            json.dump(chat_history,f,indent=2)
    except:
        pass

# ---------- INSULTI ----------
def contiene_insulto(testo):
    insulti = ["vaffanculo","idiota","scemo","cretino"]
    return any(i in testo.lower() for i in insulti)

# ---------- ARRICCHISCI PROMPT ----------
def arricchisci_prompt(prompt):

    lower = prompt.lower()

    if "cos'è" in lower or "chi è" in lower:
        arg = lower.replace("cos'è","").replace("chi è","").strip()
        info = cerca_wikipedia(arg)
        prompt += f"\ninformazioni wikipedia:\n{info}"

    if "barzelletta" in lower:
        prompt += "\nl'utente vuole una barzelletta breve."

    return prompt

# ---------- INVIO ----------
def invia_messaggio():

    global stop_generation

    prompt = txt_input.get()

    if not prompt.strip():
        return

    txt_input.delete(0, tk.END)

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,f"\n👤 TU\n{prompt}\n","utente")
    txt_chat.configure(state="disabled")

    chat_history.append({"role":"user","content":prompt})

    if len(chat_history) > MESSAGGI_MAX_HISTORY:
        chat_history.pop(0)

    salva_chat()

    stop_generation = False

    threading.Thread(target=risposta_ai,args=(prompt,)).start()

# ---------- STOP ----------
def stop_ai():
    global stop_generation
    stop_generation = True
    stop_sans_voice()

# ---------- RISPOSTA AI ----------
def risposta_ai(prompt):

    global stop_generation

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,"\n🤖 LATTINA 3000\n","bot")
    txt_chat.configure(state="disabled")

    if contiene_insulto(prompt):
        txt_chat.configure(state="normal")
        txt_chat.insert(tk.END,"heh calma amico :)\n","bot")
        txt_chat.configure(state="disabled")
        return

    full_prompt = system_prompt+"\n"

    for msg in chat_history:
        role = "User" if msg["role"]=="user" else "AI"
        full_prompt += f"{role}:{msg['content']}\n"

    full_prompt = arricchisci_prompt(full_prompt)

    try:

        with model_lock:

            with model.chat_session() as session:

                audio_started = False

                for token in session.generate(full_prompt,streaming=True):

                    if stop_generation:
                        break

                    token = token.lower()

                    txt_chat.configure(state="normal")
                    txt_chat.insert(tk.END,token,"bot")
                    txt_chat.configure(state="disabled")
                    txt_chat.see(tk.END)

                    if not audio_started:
                        threading.Thread(target=play_sans_voice_loop).start()
                        audio_started=True

    except Exception as e:

        txt_chat.configure(state="normal")
        txt_chat.insert(tk.END,f"\nErrore: {e}")
        txt_chat.configure(state="disabled")

    stop_sans_voice()

# ---------- GUI ----------
root = tk.Tk()
root.title(f"Lattina 3000 v{VERSION}")
root.geometry("760x540")
root.configure(bg="#0d0d0d")

title = tk.Label(
    root,
    text=f"█ LATTINA 3000 v{VERSION} █",
    font=("Courier",26,"bold"),
    fg="#00ffaa",
    bg="#0d0d0d"
)
title.pack(pady=12)

# ---------- CHAT ----------
frame_chat = tk.Frame(root,bg="#0d0d0d")
frame_chat.pack(fill="both",expand=True,padx=15)

txt_chat = scrolledtext.ScrolledText(
    frame_chat,
    wrap=tk.WORD,
    state="disabled",
    bg="#050505",
    fg="#e8e8e8",
    font=("Consolas",11)
)

txt_chat.tag_config("utente",foreground="#5ecbff")
txt_chat.tag_config("bot",foreground="#00ffaa")

txt_chat.pack(fill="both",expand=True)

# ---------- INPUT ----------
frame_input = tk.Frame(root,bg="#0d0d0d")
frame_input.pack(fill="x",padx=15,pady=15)

txt_input = tk.Entry(
    frame_input,
    font=("Consolas",12),
    bg="#1c1c1c",
    fg="white",
    insertbackground="white"
)

txt_input.pack(side="left",fill="x",expand=True,ipady=8)
txt_input.bind("<Return>",lambda e: invia_messaggio())

btn_invia = tk.Button(
    frame_input,
    text="INVIA",
    command=invia_messaggio,
    bg="#00ffaa",
    fg="black"
)
btn_invia.pack(side="right",padx=5)

btn_stop = tk.Button(
    frame_input,
    text="STOP",
    command=stop_ai,
    bg="#ff5555",
    fg="black"
)
btn_stop.pack(side="right")

root.mainloop()