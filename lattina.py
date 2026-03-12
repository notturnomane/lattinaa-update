# ==========================================
# LATTINA 3000
# VERSIONE 0.04
# installer + updater + memoria avanzata
# ==========================================

import os
import sys
import json
import threading
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox
from gpt4all import GPT4All
import pygame

# ==========================================
# VERSIONE
# ==========================================

VERSION = "0.04"

UPDATE_JSON = "https://raw.githubusercontent.com/notturnomane/lattinaa-update/main/version.json"

MODEL_URL = "https://huggingface.co/qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_0.gguf"

MODEL_NAME = "qwen2.5-coder-7b-instruct-q4_0.gguf"

# ==========================================
# CARTELLE
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR,"model")
MEMORY_DIR = os.path.join(BASE_DIR,"memory")

MODEL_PATH = os.path.join(MODEL_DIR,MODEL_NAME)

SHORT_MEMORY_FILE = os.path.join(MEMORY_DIR,"short_term.json")
LONG_MEMORY_FILE = os.path.join(MEMORY_DIR,"long_term.json")

VOICE_FILE = os.path.join(BASE_DIR,"sans voice.mp3")

os.makedirs(MODEL_DIR,exist_ok=True)
os.makedirs(MEMORY_DIR,exist_ok=True)

# ==========================================
# MEMORIA
# ==========================================

short_memory = []
long_memory = []

MAX_SHORT_MEMORY = 20


def carica_memoria():

    global short_memory,long_memory

    if os.path.exists(SHORT_MEMORY_FILE):

        try:
            with open(SHORT_MEMORY_FILE,"r",encoding="utf-8") as f:
                short_memory = json.load(f)
        except:
            short_memory = []

    if os.path.exists(LONG_MEMORY_FILE):

        try:
            with open(LONG_MEMORY_FILE,"r",encoding="utf-8") as f:
                long_memory = json.load(f)
        except:
            long_memory = []


def salva_memoria():

    try:

        with open(SHORT_MEMORY_FILE,"w",encoding="utf-8") as f:
            json.dump(short_memory,f,indent=2)

        with open(LONG_MEMORY_FILE,"w",encoding="utf-8") as f:
            json.dump(long_memory,f,indent=2)

    except:
        pass


def salva_memoria_lunga(info):

    long_memory.append(info)

    with open(LONG_MEMORY_FILE,"w",encoding="utf-8") as f:
        json.dump(long_memory,f,indent=2)

# ==========================================
# CONTROLLO AGGIORNAMENTI
# ==========================================

def controlla_aggiornamenti():

    try:

        r = requests.get(UPDATE_JSON,timeout=5)
        data = r.json()

        nuova_versione = data["version"]
        download = data["download"]

        if nuova_versione != VERSION:

            risposta = messagebox.askyesno(
                "Aggiornamento",
                f"Nuova versione {nuova_versione} disponibile\nAggiornare?"
            )

            if risposta:

                codice = requests.get(download).text

                with open(__file__,"w",encoding="utf-8") as f:
                    f.write(codice)

                messagebox.showinfo("Aggiornato","Riavvia il programma.")
                sys.exit()

    except:
        print("controllo aggiornamenti fallito")

# ==========================================
# DOWNLOAD MODELLO
# ==========================================

def scarica_modello():

    win = tk.Toplevel()
    win.title("Installazione modello")
    win.geometry("400x120")

    label = tk.Label(win,text="scaricando modello...")
    label.pack(pady=10)

    progress = tk.DoubleVar()

    bar = tk.Scale(win,variable=progress,from_=0,to=100,
                   orient="horizontal",length=300)

    bar.pack()

    def download():

        r = requests.get(MODEL_URL,stream=True)

        totale = int(r.headers.get("content-length",0))
        scaricato = 0

        with open(MODEL_PATH,"wb") as f:

            for chunk in r.iter_content(8192):

                if chunk:

                    f.write(chunk)

                    scaricato += len(chunk)

                    percent = scaricato*100/totale
                    progress.set(percent)

                    win.update()

        win.destroy()

    threading.Thread(target=download).start()

# ==========================================
# MODELLO
# ==========================================

def avvia_modello():

    global model

    try:

        model = GPT4All(MODEL_PATH,allow_download=False)

    except Exception as e:

        print("errore modello:",e)
        sys.exit()

# ==========================================
# AUDIO
# ==========================================

pygame.mixer.init()

def play_voice():

    try:
        pygame.mixer.music.load(VOICE_FILE)
        pygame.mixer.music.play(-1)
    except:
        pass


def stop_voice():
    pygame.mixer.music.stop()

# ==========================================
# PROMPT
# ==========================================

system_prompt = (
"sei lattina 3000 un assistente ironico "
"che parla come sans di undertale "
"scrivi sempre minuscolo"
)

# ==========================================
# AI
# ==========================================

model_lock = threading.Lock()
stop_generation = False


def costruisci_prompt(prompt):

    full = system_prompt+"\n"

    if long_memory:

        full += "\nmemoria importante:\n"

        for m in long_memory:
            full += f"- {m}\n"

    full += "\nconversazione:\n"

    for msg in short_memory:

        role = "User" if msg["role"]=="user" else "AI"

        full += f"{role}:{msg['content']}\n"

    full += f"User:{prompt}\nAI:"

    return full


def risposta_ai(prompt):

    global stop_generation

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,"\n🤖 LATTINA\n","bot")
    txt_chat.configure(state="disabled")

    full_prompt = costruisci_prompt(prompt)

    try:

        with model_lock:

            with model.chat_session() as session:

                audio=False

                for token in session.generate(full_prompt,streaming=True):

                    if stop_generation:
                        break

                    token=token.lower()

                    txt_chat.configure(state="normal")
                    txt_chat.insert(tk.END,token,"bot")
                    txt_chat.configure(state="disabled")
                    txt_chat.see(tk.END)

                    if not audio:

                        threading.Thread(target=play_voice).start()
                        audio=True

    except Exception as e:

        txt_chat.configure(state="normal")
        txt_chat.insert(tk.END,f"\nerrore:{e}")
        txt_chat.configure(state="disabled")

    stop_voice()

# ==========================================
# INVIO
# ==========================================

def invia():

    global stop_generation

    prompt = txt_input.get()

    if not prompt.strip():
        return

    txt_input.delete(0,tk.END)

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,f"\n👤 TU\n{prompt}\n","utente")
    txt_chat.configure(state="disabled")

    short_memory.append({"role":"user","content":prompt})

    if len(short_memory) > MAX_SHORT_MEMORY:
        short_memory.pop(0)

    salva_memoria()

    stop_generation=False

    threading.Thread(target=risposta_ai,args=(prompt,)).start()


def stop_ai():

    global stop_generation

    stop_generation=True
    stop_voice()

# ==========================================
# GUI
# ==========================================

root = tk.Tk()

root.title(f"LATTINA 3000 v{VERSION}")
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
txt_input.bind("<Return>",lambda e: invia())

btn_send = tk.Button(
frame_input,
text="INVIA",
command=invia,
bg="#00ffaa",
fg="black"
)

btn_send.pack(side="right",padx=5)

btn_stop = tk.Button(
frame_input,
text="STOP",
command=stop_ai,
bg="#ff5555",
fg="black"
)

btn_stop.pack(side="right")

# ==========================================
# AVVIO
# ==========================================

carica_memoria()

controlla_aggiornamenti()

if not os.path.exists(MODEL_PATH):
    scarica_modello()

avvia_modello()

root.mainloop()