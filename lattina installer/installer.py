import os
import requests
import tkinter as tk
from tkinter import ttk

MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_0.gguf"

MODEL_PATH = "models/qwen2.5-coder-7b-instruct-q4_0.gguf"


class Installer:

    def __init__(self, root):

        self.root = root
        self.root.title("Lattinaa Installer")
        self.root.geometry("400x200")

        self.label = tk.Label(root, text="Installazione Lattinaa")
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=20)

        self.status = tk.Label(root, text="")
        self.status.pack()

        self.start()

    def download_model(self):

        if os.path.exists(MODEL_PATH):
            self.status.config(text="Modello già installato")
            return

        os.makedirs("models", exist_ok=True)

        response = requests.get(MODEL_URL, stream=True)

        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(MODEL_PATH, "wb") as f:

            for data in response.iter_content(1024):

                f.write(data)
                downloaded += len(data)

                percent = downloaded / total * 100
                self.progress["value"] = percent

                self.root.update()

        self.status.config(text="Installazione completata")

    def start(self):

        self.status.config(text="Scaricamento modello AI...")

        self.download_model()


root = tk.Tk()
app = Installer(root)
root.mainloop()