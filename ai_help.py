import whisper
import sounddevice as sd
import numpy as np
import pyttsx3
import tkinter as tk
from threading import Thread
import webbrowser as web
import pyperclip

# Налаштування
DURATION = 3
SAMPLERATE = 32000
CHANNELS = 1

# Завантаження моделі
model = whisper.load_model("base")  # Можна "tiny" або "small" для швидкості
engine = pyttsx3.init()
engine.setProperty("rate", 160)

last_text = ""

# Запис аудіо
def record_audio():
    print("🎧 Записуємо...")
    audio = sd.rec(int(DURATION * SAMPLERATE), samplerate=SAMPLERATE, channels=CHANNELS, dtype='float32')
    sd.wait()
    return audio

# Розпізнавання голосу
def transcribe(audio):
    print("🧠 Розпізнаємо мовлення...")
    audio = np.squeeze(audio)
    result = model.transcribe(audio, language="uk")
    return result["text"]

# Вимова голосом
def speak(text):
    print("🤖 Відповідь:", text)
    engine.say(text)
    engine.runAndWait()

# Основна логіка
def process_audio():
    def task():
        audio = record_audio()
        text = transcribe(audio)
        print("🗣️ Співрозмовник сказав:", text)
        label.config(text=f"🗣️ {text}")

        # Можна тут підключити GPT або іншу логіку
        response = f"Ти сказав: {text}"
        speak(response)

    
    Thread(target=task).start()
    
def copy_and_open_chatgpt():
    if last_text:
        pyperclip.copy(last_text)
        web.open("https://chat.openai.com/")
    else :
        print("❗ Немає тексту для копіювання.")

# GUI
def create_gui():
    global label
    root = tk.Tk()
    root.title("🎙️ Голосовий асистент")
    root.geometry("400x250")

    label = tk.Label(root, text="Натисніть кнопку для запису голосу", wraplength=300)
    label.pack(pady=20)

    record_button = tk.Button(root, text="🎧 Записати", command=process_audio)
    record_button.pack(pady=10)
    
    copy_button = tk.Button(root, text="📋 Копіювати текст", command=copy_and_open_chatgpt)
    copy_button.pack(pady=10)

    root.mainloop()
    
if __name__ == "__main__":
    create_gui()
