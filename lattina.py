import tkinter as tk
from tkinter import scrolledtext
from gpt4all import GPT4All
import threading
import json
import os
import requests
import pygame

# ---------------- VERSIONE ----------------

VERSION = "0.05"

UPDATE_URL = "https://raw.githubusercontent.com/notturnomane/lattinaa-update/main/version.json"

# ---------------- MODELLO ----------------

MODEL_FILE = r"C:\Users\campa\Desktop\progetto\model\qwen.gguf"

# ---------------- MEMORIA ----------------

MEMORY_FOLDER = "memory"
SHORT_FILE = os.path.join(MEMORY_FOLDER,"short_term.json")
LONG_FILE = os.path.join(MEMORY_FOLDER,"long_term.json")

os.makedirs(MEMORY_FOLDER,exist_ok=True)

short_memory=[]
long_memory=[]

# ---------------- CARICA MEMORIA ----------------

def load_memory():

    global short_memory,long_memory

    try:
        with open(SHORT_FILE,"r",encoding="utf8") as f:
            short_memory=json.load(f)
    except:
        short_memory=[]

    try:
        with open(LONG_FILE,"r",encoding="utf8") as f:
            long_memory=json.load(f)
    except:
        long_memory=[]

# ---------------- SALVA MEMORIA ----------------

def save_memory():

    with open(SHORT_FILE,"w",encoding="utf8") as f:
        json.dump(short_memory,f,indent=2)

    with open(LONG_FILE,"w",encoding="utf8") as f:
        json.dump(long_memory,f,indent=2)

# ---------------- RESET SHORT MEMORY ----------------

def reset_short():

    global short_memory

    short_memory=[]

    save_memory()

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,"\n[memoria breve cancellata]\n")
    txt_chat.configure(state="disabled")

# ---------------- CONTROLLO UPDATE ----------------

def check_updates():

    try:

        data=requests.get(UPDATE_URL,timeout=5).json()

        latest=data["version"]

        if latest!=VERSION:

            txt_chat.configure(state="normal")
            txt_chat.insert(tk.END,f"\n⚠ nuova versione disponibile {latest}\n")
            txt_chat.insert(tk.END,f"{data['notes']}\n")
            txt_chat.configure(state="disabled")

    except:
        print("controllo aggiornamenti fallito")

# ---------------- AUDIO ----------------

pygame.mixer.init()

def play_voice():

    try:
        pygame.mixer.music.load("sans voice.mp3")
        pygame.mixer.music.play(-1)
    except:
        pass

def stop_voice():
    pygame.mixer.music.stop()

# ---------------- MODELLO ----------------

try:

    model=GPT4All(
        model_name=MODEL_FILE,
        allow_download=False
    )

except Exception as e:

    print("errore modello:",e)
    exit()

model_lock=threading.Lock()

# ---------------- PROMPT ----------------

SYSTEM_PROMPT="""
sei lattina 3000
parli come sans
scrivi minuscolo
sei ironico
"""

# ---------------- STOP AI ----------------

stop_generation=False

def stop_ai():

    global stop_generation

    stop_generation=True
    stop_voice()

# ---------------- COSTRUISCI PROMPT ----------------

def build_prompt():

    prompt=SYSTEM_PROMPT+"\n"

    for m in long_memory:
        prompt+=f"memory:{m}\n"

    for m in short_memory:

        role="User" if m["role"]=="user" else "AI"

        prompt+=f"{role}:{m['content']}\n"

    return prompt

# ---------------- INVIA ----------------

def send_message():

    global stop_generation

    msg=txt_input.get()

    if not msg.strip():
        return

    txt_input.delete(0,tk.END)

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,f"\n👤 tu\n{msg}\n","user")
    txt_chat.configure(state="disabled")

    short_memory.append({"role":"user","content":msg})

    save_memory()

    stop_generation=False

    threading.Thread(target=ai_reply).start()

# ---------------- RISPOSTA AI ----------------

def ai_reply():

    global stop_generation

    txt_chat.configure(state="normal")
    txt_chat.insert(tk.END,"\n🤖 lattina\n","bot")
    txt_chat.configure(state="disabled")

    prompt=build_prompt()

    answer=""

    try:

        with model_lock:

            with model.chat_session() as session:

                audio_started=False

                for token in session.generate(
                    prompt,
                    temp=0.6,
                    top_k=40,
                    top_p=0.9,
                    repeat_penalty=1.2,
                    streaming=True
                ):

                    if stop_generation:
                        break

                    answer+=token

                    txt_chat.configure(state="normal")
                    txt_chat.insert(tk.END,token,"bot")
                    txt_chat.configure(state="disabled")
                    txt_chat.see(tk.END)

                    if not audio_started:

                        threading.Thread(target=play_voice).start()
                        audio_started=True

    except Exception as e:

        txt_chat.configure(state="normal")
        txt_chat.insert(tk.END,str(e))
        txt_chat.configure(state="disabled")

    stop_voice()

    short_memory.append({"role":"assistant","content":answer})

    save_memory()

# ---------------- GUI ----------------

root=tk.Tk()

root.title(f"Lattina 3000 v{VERSION}")

root.geometry("760x540")

txt_chat=scrolledtext.ScrolledText(root,state="disabled")
txt_chat.pack(fill="both",expand=True)

txt_chat.tag_config("user",foreground="cyan")
txt_chat.tag_config("bot",foreground="lime")

frame=tk.Frame(root)
frame.pack(fill="x")

txt_input=tk.Entry(frame)
txt_input.pack(side="left",fill="x",expand=True)

txt_input.bind("<Return>",lambda e:send_message())

btn_send=tk.Button(frame,text="INVIA",command=send_message)
btn_send.pack(side="right")

btn_stop=tk.Button(frame,text="STOP",command=stop_ai)
btn_stop.pack(side="right")

btn_reset=tk.Button(root,text="RESET MEMORIA BREVE",command=reset_short)
btn_reset.pack()

load_memory()

threading.Thread(target=check_updates).start()

root.mainloop()