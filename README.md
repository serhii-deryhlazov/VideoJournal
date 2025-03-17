# Video Journal Recorder

A simple Python application to record video and audio simultaneously using your webcam and microphone, merging them into a single `.mp4` file. Built with OpenCV, PyAudio, FFmpeg, and Tkinter for a graphical interface.

## Features
- Live webcam preview with adjustable aspect ratio.
- Record video (at 15 FPS) and audio (44.1 kHz, mono).
- Save recordings to a `records/` directory with timestamps.
- List previous recordings in the UI.

## Prerequisites
- **Python 3.13** (or compatible version).
- A webcam and microphone connected to your system.
- FFmpeg installed and accessible from the command line.

## Setup Instructions

### 1. Clone or Download the Repository

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
On Windows, use:
```bash
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install opencv-python Pillow screeninfo pyaudio ffmpeg-python
```
### 4. Install FFmpeg
```bash
brew install ffmpeg
```
On Windows, download from ffmpeg.org and add to PATH.
### 5. Run the Application
```bash
python journal.py
```

## Usage
- Click "Record" to start recording.
- Click "Stop Recording" to save the `.mp4` file to `records/`.
- View previous recordings in the right panel.