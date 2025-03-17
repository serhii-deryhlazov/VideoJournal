import pyaudio
import wave
import os

def test_microphone():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5
    OUTPUT_FILENAME = "test_audio.wav"

    print("Testing microphone access...")
    
    try:
        p = pyaudio.PyAudio()
        print("Available audio devices:")
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            print(f"Device {i}: {device_info['name']}, Input Channels: {device_info['maxInputChannels']}")

        # Replace with the correct device index if needed
        AUDIO_DEVICE_INDEX = 0  # Update based on available devices
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=AUDIO_DEVICE_INDEX)
        print(f"\nRecording audio for {RECORD_SECONDS} seconds using device index {AUDIO_DEVICE_INDEX}...")
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        print("Recording complete.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"Audio saved as {OUTPUT_FILENAME}.")
        print("Please play the file to verify audio was recorded.")
        return True
    except Exception as e:
        print("Error recording audio:", str(e))
        print("\nTroubleshooting steps:")
        print("- Ensure microphone permissions are granted (macOS: System Settings > Privacy & Security > Microphone).")
        print("- Check if the microphone is in use by another application.")
        print("- Verify the microphone is not muted or disabled.")
        print("- Try specifying a different input device index (see available devices above).")
        return False

if __name__ == "__main__":
    test_microphone()
