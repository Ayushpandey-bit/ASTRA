import pyaudio
import numpy as np
from openwakeword.model import Model
import openwakeword

# Download pre-trained models (only happens once)
openwakeword.utils.download_models()

# Load the "hey jarvis" wake word model
model = Model(wakeword_models=["hey_jarvis"])

CHUNK = 1280  # required chunk size for openWakeWord
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK,
                     input_device_index=1)  # your mic device

print("Listening for 'Hey Jarvis'... (Ctrl+C to stop)")

while True:
    audio_data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    prediction = model.predict(audio_data)

    for wakeword, score in prediction.items():
        if score > 0.5:
            print(f"Wake word detected! ({wakeword}, confidence: {score:.2f})")