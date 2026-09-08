import time
import pyaudio
import numpy as np
from openwakeword.model import Model


class WakeWordDetector:

    def __init__(self):
        print("Loading Hey Astra V2 wake word model...")

        # Load custom V2 model
        self.model = Model(
            wakeword_models=["models/hey_astra_v2.onnx"],
            inference_framework="onnx"
        )

        # Audio settings
        self.CHUNK = 1280
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        # Detection settings
        self.THRESHOLD = 0.5
        self.COOLDOWN = 1.5

        # Used to prevent multiple detections
        self.cooldown_until = 0

        # Start PyAudio
        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            input_device_index=1
        )

        print("Hey Astra V2 detector ready.")
        print("Say: Hey Astra")

    def listen(self):

        # Read microphone audio
        audio_data = np.frombuffer(
            self.stream.read(
                self.CHUNK,
                exception_on_overflow=False
            ),
            dtype=np.int16
        )

        # Get model prediction
        prediction = self.model.predict(audio_data)

        # Get Hey Astra score
        score = prediction.get("hey_astra_v2", 0.0)

        print(f"Hey Astra score: {score:.4f}")

        # Check cooldown
        if time.time() < self.cooldown_until:
            return False

        # Wake word detected
        if score > self.THRESHOLD:

            print(">>> HEY ASTRA DETECTED! <<<")

            # Start cooldown
            self.cooldown_until = time.time() + self.COOLDOWN

            return True

        return False

    def close(self):

        print("Stopping wake word detector...")

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()


# ==============
# MAIN PROGRAM
# ==============

if __name__ == "__main__":

    detector = WakeWordDetector()

    try:

        print("Listening for Hey Astra...")

        while True:
            detected = detector.listen()

            if detected:
                # This is where the actual Astra assistant
                # will eventually be triggered.
                pass

    except KeyboardInterrupt:

        print("\nStopping...")

    finally:

        detector.close()