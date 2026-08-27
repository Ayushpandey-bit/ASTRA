import sounddevice as sd
import numpy as np
def record_until_silence(
    samplerate=44100,
    silence_threshold=0.02,
    silence_duration=1.5,
    max_duration=30
):
    recorded_frames = []
    silent_time = 0
    started_talking = False
    block_duration = 0.2
    block_samples = int(samplerate * block_duration)

    stream = sd.InputStream(
        samplerate=samplerate,
        channels=1,
        device=1
    )

    stream.start()

    elapsed = 0

    while elapsed < max_duration:
        block, _ = stream.read(block_samples)
        recorded_frames.append(block)

        volume = np.abs(block).mean()

        if volume > silence_threshold:
            started_talking = True
            silent_time = 0
        elif started_talking:
            silent_time += block_duration

        if started_talking and silent_time >= silence_duration:
            break

        elapsed += block_duration

    stream.stop()
    stream.close()

    return np.concatenate(recorded_frames, axis=0)