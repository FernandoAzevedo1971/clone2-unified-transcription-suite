import sounddevice as sd
import time
def callback(indata, frames, time_info, status):
    print("Callback called, frames:", frames, "status:", status)
try:
    # Try device index 1 (USB Mic)
    stream = sd.RawInputStream(samplerate=44100, channels=1, dtype='int16', device=1, callback=callback)
    with stream:
        print("Stream started")
        time.sleep(2)
    print("Stream finished")
except Exception as e:
    print(f"Error: {e}")
