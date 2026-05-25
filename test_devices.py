import sounddevice as sd

with open('device_test_results.txt', 'w', encoding='utf-8') as f:
    for i, dev in enumerate(sd.query_devices()):
        if dev.get('max_input_channels', 0) > 0:
            f.write(f"Testing Device Index {i}: {dev['name']} [HostAPI {dev['hostapi']}]\n")
            f.write(f"  Max In Channels: {dev['max_input_channels']}, Default SR: {dev['default_samplerate']}\n")
            
            # Try our app's defaults (44100 Hz, 1 channel)
            try:
                stream = sd.RawInputStream(
                    samplerate=44100,
                    channels=1,
                    device=i,
                    dtype='int16'
                )
                stream.close()
                f.write("  Result (44100, 1ch): SUCCESS\n")
            except Exception as e:
                f.write(f"  Result (44100, 1ch): FAILED - {e}\n")
                
            # Try device defaults
            try:
                stream = sd.RawInputStream(
                    samplerate=int(dev['default_samplerate']),
                    channels=min(1, int(dev['max_input_channels'])),
                    device=i,
                    dtype='int16'
                )
                stream.close()
                f.write(f"  Result ({dev['default_samplerate']}, 1ch): SUCCESS\n")
            except Exception as e:
                f.write(f"  Result ({dev['default_samplerate']}, 1ch): FAILED - {e}\n")
            
            f.write("-" * 40 + "\n")
