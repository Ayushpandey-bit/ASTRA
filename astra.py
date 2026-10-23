import time
import whisper
from ai.memory import Memory
from audio.speaker import speak
from audio.recorder import record_until_silence
from scipy.io.wavfile import write
from commands.router import try_handle_command
import pyaudio
from openwakeword.model import Model
import numpy as np
from ai.brain import ask_ai


memory = Memory()

print("Loading Whisper model...")
whisper_model = whisper.load_model("small")

print("Loading Hey Astra V2 wake word model...")
ww_model = Model(
    wakeword_models=["models/hey_astra_v2.onnx"],
    inference_framework="onnx"
)

samplerate = 44100

CHUNK = 1280
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

WAKE_WORD_THRESHOLD = 0.50
WAKE_WORD_CONFIRMATIONS = 3
WAKE_WORD_COOLDOWN = 2.0

wake_confirmations = 0
last_trigger_time = 0

audio = pyaudio.PyAudio()

ww_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=1
)

print()
print("Astra is ready. Say 'Hey Astra'.")
print()


def process_command():
    recording = record_until_silence(
        samplerate=samplerate
    )

    write(
        "mic_input.wav",
        samplerate,
        recording
    )

    print("Transcribing...")

    result = whisper_model.transcribe(
        "mic_input.wav"
    )

    user_text = result["text"].strip()

    print("You said:", user_text)
    print(f"[DEBUG] Raw transcription: '{user_text}'")

    if not user_text:
        return False

    memory.save(
        "user",
        user_text
    )

    if "stop" in user_text.lower():
        speak("Goodbye!")
        return True

    command_result = try_handle_command(
        user_text
    )

    if command_result:
        print("Astra:", command_result)
        speak(command_result)
        return False

    print("Thinking...")

    history = memory.get_recent()

    astra_reply = ask_ai(
        user_text,
        history
    )

    print("Astra:", astra_reply)

    memory.save(
        "assistant",
        astra_reply
    )

    speak(astra_reply)

    print("[DEBUG] Finished speaking.")
    print()

    return False


try:
    while True:

        audio_data = np.frombuffer(
            ww_stream.read(
                CHUNK,
                exception_on_overflow=False
            ),
            dtype=np.int16
        )

        prediction = ww_model.predict(audio_data)

        wake_score = prediction.get(
            "hey_astra_v2",
            0.0
        )

        print(f"[Wake word] {wake_score:.4f}")

        current_time = time.time()

        if current_time - last_trigger_time < WAKE_WORD_COOLDOWN:
            wake_confirmations = 0
            continue

        if wake_score >= WAKE_WORD_THRESHOLD:
            wake_confirmations += 1
        else:
            wake_confirmations = 0

        if wake_confirmations < WAKE_WORD_CONFIRMATIONS:
            continue

        wake_confirmations = 0
        last_trigger_time = current_time

        print()
        print(">>> HEY ASTRA DETECTED! <<<")
        print()

        speak("Yes?")

        while True:

            print("Listening...")

            should_stop = process_command()

            if should_stop:
                raise KeyboardInterrupt

            print("Ready for another command...")

            time.sleep(0.3)


except KeyboardInterrupt:

    print()
    print("Stopping Astra...")


finally:

    ww_stream.stop_stream()
    ww_stream.close()
    audio.terminate()

    print("Astra stopped.")