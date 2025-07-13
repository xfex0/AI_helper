import whisper
import sounddevice as sd
import numpy as np
import pyttsx3
import tkinter as tk
from threading import Thread
import webbrowser as web
import pyperclip
import queue
import torch 
import webrtcvad
import collections
import sys
import numpy as np

# Налаштування
DURATION = 3
SAMPLERATE = 32000
CHANNELS = 1

speak_queue = queue.Queue()
model = whisper.load_model("large")  # Можна "tiny" або "small" для швидкості
engine = pyttsx3.init()
engine.setProperty("rate", 160)
last_text = ""
vad = webrtcvad.Vad(2)  # 0-3
# Вимова голосом
def speak_async():
    while True:
        text = speak_queue.get()
        if text is None:
            break
    print("🤖 Відповідь:", text)
    engine.say(text)
    engine.runAndWait()    
    
# Запис аудіо
def record_audio():
    print("🎧 Записуємо...")
    audio = sd.rec(int(DURATION * SAMPLERATE), samplerate=SAMPLERATE, channels=CHANNELS, dtype='float32')
    sd.wait()
    return audio

def frame_generator(audio, frame_duration_ms=30, sample_rate=SAMPLERATE):
    n = int(sample_rate * frame_duration_ms / 1000) * 2 
    offset = 0  
    while offset + n < len(audio):
        yield audio[offset:offset + n]
        offset += n
        
def vad_collector(sample_rate, frame_duration_ms, padding_duration_ms, audio):
    frames = frame_generator(audio, frame_duration_ms, sample_rate)
    vad = webrtcvad.Vad(2)  # 0-3
    padding_frames = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=padding_frames)
    triggered = False
    voiced_frames = []

    for frame in frames:
        is_speech = vad.is_speech(frame, sample_rate)
        if not triggered:
            if is_speech:
                triggered = True
                voiced_frames.append(frame)
                ring_buffer.clear()
            else:
                ring_buffer.append(frame)
        else:
            voiced_frames.append(frame)
            if not is_speech:
                ring_buffer.append(frame)
                if len(ring_buffer) == padding_frames:
                    triggered = False
                    yield b''.join(voiced_frames)
                    voiced_frames = []
                    ring_buffer.clear()
    
    if voiced_frames:
        yield b''.join(voiced_frames)

# Розпізнавання голосу
def transcribe(audio):
    print("🧠 Розпізнаємо мовлення...")
    audio = np.squeeze(audio)
    result = model.transcribe(audio, language="uk")
    return result["text"]

# Основна логіка
def process_audio():
    def task():
        global last_text
        audio = record_audio()
        text = transcribe(audio)
        last_text = text.strip()
        if not text:
            print("❗ Нічого не розпізнано.")
            return    
        print("🗣️ Співрозмовник сказав:", text)
        label.config(text=f"🗣️ {text}")

        # Можна тут підключити GPT 
        response = f"Ти сказав: {text}"
        speak_queue.put(response)     
    
    Thread(target=task, daemon=True).start()
    
    
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
    
    stop_button = tk.Button(root, text = "❌ Вийти", command=root.quit)
    stop_button.pack(pady=10)
    
    root.mainloop()
    
if __name__ == "__main__":
    Thread(target=speak_async, daemon=True).start()
    create_gui()
