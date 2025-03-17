import tkinter as tk
from tkinter import ttk
import cv2
import os
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk
import screeninfo
import pyaudio
import wave
import ffmpeg

class VideoJournal:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Journal")
        
        # Get screen dimensions
        screen = screeninfo.get_monitors()[0]
        screen_width = screen.width
        screen_height = screen.height
        
        # Calculate window size (80% of screen size)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{int((screen_width-window_width)/2)}+{int((screen_height-window_height)/2)}")
        self.root.resizable(False, False)  # Disable window resizing
        
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=8)  # 80% for preview
        self.root.grid_columnconfigure(1, weight=2)  # 20% for records
        
        # Create records directory if it doesn't exist
        self.records_dir = "records"
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)
            
        # Initialize webcam with the built-in camera index
        BUILT_IN_CAMERA_INDEX = 0  # Confirmed from test_webcam.py
        self.cap = cv2.VideoCapture(BUILT_IN_CAMERA_INDEX)
        print(f"Trying built-in webcam (index {BUILT_IN_CAMERA_INDEX})...")
        print(f"Webcam opened (index {BUILT_IN_CAMERA_INDEX}):", self.cap.isOpened())
        
        if not self.cap.isOpened():
            print("Error: Could not open built-in webcam. Check permissions and connections.")
            tk.messagebox.showerror("Error", "Could not open built-in webcam. Check permissions and connections.")
            self.root.destroy()
            return
        
        # Get webcam properties
        self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cam_fps = 15  # Hardcode to 30 FPS (common for MacBook webcams)
        self.cam_aspect_ratio = self.cam_width / self.cam_height
        print(f"Webcam resolution: {self.cam_width}x{self.cam_height}, FPS set to: {self.cam_fps}")
        
        self.is_recording = False
        self.video_out = None
        self.audio_thread = None
        self.audio_out = None
        self.audio_stream = None
        self.audio_p = None
        self.video_start_time = None
        self.audio_start_time = None
        
        # Create main containers
        self.preview_frame = tk.Frame(self.root, width=window_width*0.8, height=window_height)
        self.preview_frame.grid(row=0, column=0, sticky="nsew")
        
        self.records_frame = tk.Frame(self.root, width=window_width*0.2, height=window_height, bg="#333333")  # Dark grey background
        self.records_frame.grid(row=0, column=1, sticky="nsew")
        
        # Preview panel (left 80%) - Adjust to webcam aspect ratio
        self.video_label = tk.Label(self.preview_frame, bg="black")  # Black background for letterboxing
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Record button
        self.record_button = ttk.Button(self.preview_frame, text="Record", command=self.toggle_recording)
        self.record_button.place(relx=0.5, rely=0.95, anchor="s")
        
        # Records list (right 20%)
        tk.Label(self.records_frame, text="Previous Recordings", bg="#333333", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.records_listbox = tk.Listbox(self.records_frame, bg="#444444", fg="white", font=("Arial", 10), selectbackground="#555555")
        self.records_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Populate records list
        self.update_records_list()
        
        # Start video feed after GUI is rendered
        self.root.after(100, self.update_video_feed)  # Delay initial update
    
    def update_records_list(self):
        self.records_listbox.delete(0, tk.END)
        records = [f for f in os.listdir(self.records_dir) if f.endswith('.mp4')]
        records.sort(reverse=True)
        for record in records:
            self.records_listbox.insert(tk.END, record)
    
    def start_audio_recording(self, audio_filename):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        try:
            self.audio_p = pyaudio.PyAudio()
            print("Available audio devices:")
            for i in range(self.audio_p.get_device_count()):
                device_info = self.audio_p.get_device_info_by_index(i)
                print(f"Device {i}: {device_info['name']}, Input Channels: {device_info['maxInputChannels']}")
            
            # Use the confirmed device index from test_microphone.py
            AUDIO_DEVICE_INDEX = 0  # MacBook Air Microphone
            print(f"Using audio device index {AUDIO_DEVICE_INDEX}")
            self.audio_stream = self.audio_p.open(format=FORMAT,
                                                channels=CHANNELS,
                                                rate=RATE,
                                                input=True,
                                                frames_per_buffer=CHUNK,
                                                input_device_index=AUDIO_DEVICE_INDEX)
            print("Audio stream opened successfully.")
            
            self.audio_out = wave.open(audio_filename, 'wb')
            self.audio_out.setnchannels(CHANNELS)
            self.audio_out.setsampwidth(self.audio_p.get_sample_size(FORMAT))
            self.audio_out.setframerate(RATE)
            print(f"Audio file {audio_filename} opened for writing.")
            
            def record_audio():
                print("Audio recording thread started.")
                self.audio_start_time = time.time()  # Record audio start time
                while self.is_recording:
                    try:
                        data = self.audio_stream.read(CHUNK, exception_on_overflow=False)
                        self.audio_out.writeframes(data)
                    except Exception as e:
                        print("Error in audio recording thread:", str(e))
                        break
                print("Audio recording thread stopped.")
            
            self.audio_thread = threading.Thread(target=record_audio)
            self.audio_thread.start()
            time.sleep(0.1)  # Small delay to ensure thread starts
            print("Audio recording started.")
        except Exception as e:
            print("Error starting audio recording:", str(e))
            tk.messagebox.showerror("Error", "Could not start audio recording. Check microphone permissions and connections.")
    
    def stop_audio_recording(self):
        self.is_recording = False
        if self.audio_thread:
            try:
                print("Waiting for audio thread to stop...")
                self.audio_thread.join()  # Wait for thread to finish
                print("Audio thread joined.")
            except Exception as e:
                print("Error joining audio thread:", str(e))
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                print("Audio stream stopped.")
                self.audio_stream.close()
                print("Audio stream closed.")
            except Exception as e:
                print("Error stopping audio stream:", str(e))
        if self.audio_out:
            try:
                self.audio_out.close()
                print("Audio file closed.")
            except Exception as e:
                print("Error closing audio file:", str(e))
        if self.audio_p:
            try:
                self.audio_p.terminate()
                print("PyAudio terminated.")
            except Exception as e:
                print("Error terminating PyAudio:", str(e))
        print("Audio recording fully stopped.")
    
    def merge_audio_video(self, video_filename, audio_filename, output_filename):
        try:
            if not os.path.exists(video_filename):
                print(f"Error: Video file {video_filename} missing for merging.")
                return
            if not os.path.exists(audio_filename):
                print(f"Error: Audio file {audio_filename} missing for merging.")
                return
            audio_size = os.path.getsize(audio_filename)
            if audio_size < 100:  # Check if audio file is too small (likely empty)
                print(f"Error: Audio file {audio_filename} is empty or too small ({audio_size} bytes).")
                return
            
            # Calculate delay between video and audio start times
            if self.video_start_time and self.audio_start_time:
                delay = self.audio_start_time - self.video_start_time
                print(f"Calculated delay: {delay:.3f} seconds (audio starts after video)")
            else:
                delay = 0
                print("Warning: Start times not recorded, using delay=0")
            
            print(f"Merging video ({video_filename}) and audio ({audio_filename}) into {output_filename}")
            video_stream = ffmpeg.input(video_filename, itsoffset=delay if delay > 0 else 0)
            audio_stream = ffmpeg.input(audio_filename)
            # Use vcodec='copy' and let FFmpeg infer frame rate from input
            ffmpeg.output(video_stream, audio_stream, output_filename, 
                        vcodec='copy', acodec='aac', vsync='vfr').run(overwrite_output=True)
            print(f"Audio and video merged into {output_filename}")
            os.remove(video_filename)  # Remove temporary video file
            os.remove(audio_filename)  # Remove temporary audio file
        except ffmpeg.Error as e:
            print("Error merging audio and video:", e.stderr if e.stderr else "No stderr available")
            tk.messagebox.showerror("Error", "Could not merge audio and video. Check FFmpeg installation.")
    
    def toggle_recording(self):
        if not self.is_recording:
            # Reset timestamps
            self.video_start_time = None
            self.audio_start_time = None
            
            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_video_filename = os.path.join(self.records_dir, f"temp_video_{timestamp}.mp4")
            temp_audio_filename = os.path.join(self.records_dir, f"temp_audio_{timestamp}.wav")
            final_filename = os.path.join(self.records_dir, f"journal_{timestamp}.mp4")
            
            # Initialize video writer with fixed FPS
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_out = cv2.VideoWriter(temp_video_filename, fourcc, self.cam_fps, (self.cam_width, self.cam_height))
            self.video_start_time = time.time()  # Record video start time
            print(f"Video recording started: {temp_video_filename} at {self.cam_fps} FPS")
            
            # Start audio recording
            self.is_recording = True
            self.start_audio_recording(temp_audio_filename)
            
            self.record_button.configure(text="Stop Recording", style='Accent.TButton')
            self.temp_video_filename = temp_video_filename
            self.temp_audio_filename = temp_audio_filename
            self.final_filename = final_filename
        else:
            # Stop recording
            self.is_recording = False
            if self.video_out:
                self.video_out.release()
                self.video_out = None
                print("Video recording stopped.")
            self.stop_audio_recording()
            
            # Merge audio and video
            self.merge_audio_video(self.temp_video_filename, self.temp_audio_filename, self.final_filename)
            
            self.record_button.configure(text="Record", style='TButton')
            self.update_records_list()
    
    def update_video_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            self.root.after(10, self.update_video_feed)
            return
        
        # Convert frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # If recording, write frame to video
        if self.is_recording and self.video_out:
            self.video_out.write(frame)
        
        # Calculate preview dimensions while maintaining aspect ratio
        preview_width = self.preview_frame.winfo_width()
        preview_height = self.preview_frame.winfo_height()
        
        # Ensure dimensions are valid
        if preview_width <= 0 or preview_height <= 0:
            print("Warning: Preview dimensions not yet available. Retrying...")
            self.root.after(10, self.update_video_feed)
            return
        
        preview_aspect_ratio = preview_width / preview_height
        
        if preview_aspect_ratio > self.cam_aspect_ratio:
            # Preview is wider than camera - fit to height
            new_height = preview_height
            new_width = int(new_height * self.cam_aspect_ratio)
        else:
            # Preview is taller than camera - fit to width
            new_width = preview_width
            new_height = int(new_width / self.cam_aspect_ratio)
        
        # Ensure new dimensions are positive
        if new_width <= 0 or new_height <= 0:
            print(f"Error: Invalid resize dimensions ({new_width}x{new_height}). Retrying...")
            self.root.after(10, self.update_video_feed)
            return
        
        # Resize frame
        frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        image = Image.frombytes('RGB', (frame_rgb.shape[1], frame_rgb.shape[0]), frame_rgb)
        photo = ImageTk.PhotoImage(image=image)
        
        # Update video label
        self.video_label.configure(image=photo)
        self.video_label.image = photo
        
        # Schedule next update
        self.root.after(10, self.update_video_feed)
    
    def on_closing(self):
        # Release resources
        if self.is_recording:
            self.is_recording = False
            if self.video_out:
                self.video_out.release()
                print("Video recording stopped on close.")
            self.stop_audio_recording()
            self.merge_audio_video(self.temp_video_filename, self.temp_audio_filename, self.final_filename)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # Configure styles
    style = ttk.Style()
    style.configure('Accent.TButton', background='red', foreground='white')
    
    app = VideoJournal(root)
    root.mainloop()

if __name__ == "__main__":
    main()
