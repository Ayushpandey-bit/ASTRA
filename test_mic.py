import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import time

duration = 5
samplerate = 44100

print("Get ready to speak...")
time.sleep(2)
print("Listening... speak now!")

recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, device=1)
sd.wait()

# Check if we actually captured sound
volume = np.abs(recording).mean()
print(f"Average volume level: {volume}")

write("mic_input.wav", samplerate, recording)
print("Recording saved.")