import sounddevice as sd
import time
import sys

def test_device(device_idx, name):
    log_file = open("callback_log.txt", "a")
    log_file.write(f"\n--- Testing Device {device_idx}: {name} ---\n")
    called = False
    
    def callback(indata, frames, time_info, status):
        nonlocal called
        called = True
    
    try:
        # Try finding a supported sample rate
        dev_info = sd.query_devices(device_idx)
        sr = int(dev_info.get('default_samplerate', 44100))
        if sr == 0: sr = 44100
        
        stream = sd.RawInputStream(samplerate=sr, channels=1, dtype='int16', blocksize=1024, device=device_idx, callback=callback)
        with stream:
            time.sleep(1)
        
        if called:
            log_file.write(f"SUCCESS: Callback WAS called for device {device_idx}\n")
        else:
            log_file.write(f"FAILED: Callback NOT called for device {device_idx}\n")
    except Exception as e:
        log_file.write(f"Error for device {device_idx}: {e}\n")
    
    log_file.close()

open("callback_log.txt", "w").close() # Clear file

for i, dev in enumerate(sd.query_devices()):
    if dev.get('max_input_channels', 0) > 0:
        test_device(i, dev['name'])
