import sounddevice as sd
import numpy as np
import whisper
import win32clipboard
import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhisperRecorder:
    def __init__(self, model_name: str = "small", sample_rate: int = 16000, channels: int = 1):
        self.SAMPLE_RATE = sample_rate
        self.CHANNELS = channels
        self.BUFFER = []
        self.model_name = model_name
        self.stream = None
        self.is_recording = False
        self.start_time = 0
        self.model = None
        self.audio_level = 0  # Add audio level tracking

    def load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def callback(self, indata, frames, time, status):
        """Callback function for sounddevice stream"""
        if status:
            logger.warning(f"Audio stream status: {status}")
        self.BUFFER.append(indata.copy())
        # Calculate audio level (RMS)
        self.audio_level = np.sqrt(np.mean(indata**2))

    def start_recording(self):
        """Start recording audio"""
        try:
            self.stream = sd.InputStream(samplerate=self.SAMPLE_RATE, channels=self.CHANNELS, dtype='float32', callback=self.callback)
            self.stream.start()
            self.is_recording = True
            self.start_time = time.time()
            logger.info("🎙️ Recording started...")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise

    def stop_recording(self):
        """Stop recording and return the audio data"""
        if not self.is_recording:
            return None

        self.stream.stop()
        self.stream.close()
        self.is_recording = False
        
        duration = time.time() - self.start_time
        logger.info(f"✅ Recording stopped. Duration: {duration:.1f} seconds")
        
        if not self.BUFFER:
            logger.warning("No audio data was recorded")
            return None

        # Concatenate all chunks
        audio_data = np.concatenate(self.BUFFER, axis=0).flatten()
        self.BUFFER = []  # Clear buffer for next recording
        return audio_data

    def transcribe(self, audio_data):
        """Transcribe audio data using Whisper"""
        if audio_data is None:
            return ""

        try:
            logger.info("Transcribing audio...")
            result = self.model.transcribe(audio_data, fp16=False)
            return result["text"]
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""

def copy_to_clipboard(text: str):
    """Copy text to Windows clipboard"""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")

class WhisperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window position
        window_width = 1200
        window_height = 150
        x_position = (screen_width - window_width) // 2  # Center horizontally
        y_position = screen_height // 3  # First third from top
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Add keyboard bindings
        self.root.bind('<space>', lambda e: self.toggle_recording())
        self.root.bind('<Return>', lambda e: self.toggle_recording())

        # Load the Whisper model
        self.recorder = WhisperRecorder(model_name="small")
        self.recorder.load_model()

        # Load icons
        self.load_icons()

        # Create GUI elements
        self.create_widgets()

    def load_icons(self):
        """Load and prepare icons for the application"""
        try:
            # Create icons directory if it doesn't exist
            if not os.path.exists('icons'):
                os.makedirs('icons')
                logger.info("Created icons directory")

            # Initialize icons dictionary
            self.icons = {}

            # Load record button icon
            record_path = os.path.abspath('icons/record.png')
            logger.info(f"Loading record button from: {record_path}")
            if os.path.exists(record_path):
                record_img = Image.open(record_path)
                record_img = record_img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icons['record'] = ImageTk.PhotoImage(record_img)
                logger.info("Record button loaded successfully")
            else:
                logger.error(f"Record button not found at: {record_path}")

            # Load microphone icon
            mic_path = os.path.abspath('icons/mic.png')
            logger.info(f"Loading microphone icon from: {mic_path}")
            if os.path.exists(mic_path):
                mic_img = Image.open(mic_path)
                mic_img = mic_img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icons['mic'] = ImageTk.PhotoImage(mic_img)
                logger.info("Microphone icon loaded successfully")
            else:
                logger.error(f"Microphone icon not found at: {mic_path}")

        except Exception as e:
            logger.error(f"Failed to load icons: {e}")
            # Create fallback icons
            self.icons = {
                'record': None,
                'mic': None
            }

    def create_widgets(self):
        # Use ttk for native Windows look
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 16))
        style.configure("TLabel", font=("Segoe UI", 10), background='#2b2b2b', foreground='white')
        style.configure("TFrame", background='#2b2b2b')

        # Main frame
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top frame for button, status and visualizer
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        # Left frame for button and status
        left_frame = ttk.Frame(top_frame)
        left_frame.pack(side=tk.LEFT, padx=5)

        # Record button with icon
        self.record_button = ttk.Button(
            left_frame,
            text="🔴",  # Fallback emoji
            width=3,
            command=self.toggle_recording
        )
        if self.icons.get('record'):
            self.record_button.configure(image=self.icons['record'])
        self.record_button.pack(side=tk.LEFT)

        # Status label
        self.status_label = ttk.Label(
            left_frame,
            text="Ready to record",
            font=("Segoe UI", 10),
            foreground='white'
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Text box for transcription with custom styling
        self.text_box = tk.Text(
            main_frame,
            wrap=tk.WORD,
            width=60,  # Adjusted for wider window
            height=8,  # Reduced height for shorter window
            font=("Segoe UI", 10),
            bg='#2b2b2b',
            fg='white',
            relief=tk.FLAT,
            highlightthickness=0,
            padx=5,
            pady=5,
            insertbackground='white'
        )
        self.text_box.pack(pady=5, fill=tk.BOTH, expand=True)

        # Configure text box tags for better appearance
        self.text_box.tag_configure("default", foreground="white")
        self.text_box.tag_add("default", "1.0", tk.END)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.record_button.configure(image=self.icons['mic'])
        self.status_label.configure(text="Recording...")
        threading.Thread(target=self._record, daemon=True).start()

    def _record(self):
        try:
            self.recorder.start_recording()
        except Exception as e:
            self.record_button.configure(image=self.icons['record'])
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, f"Error: {e}")

    def stop_recording(self):
        self.record_button.configure(image=self.icons['record'])
        self.status_label.configure(text="Generating text...")
        threading.Thread(target=self._stop_and_transcribe, daemon=True).start()

    def _stop_and_transcribe(self):
        try:
            audio_data = self.recorder.stop_recording()
            if audio_data is not None:
                text = self.recorder.transcribe(audio_data)
                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, text)
                copy_to_clipboard(text)
                self.status_label.configure(text="Ready to record")
                logger.info("✅ Transcription completed and copied to clipboard")
            else:
                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, "No audio recorded")
                self.status_label.configure(text="Ready to record")
                logger.warning("No audio was recorded")
        except Exception as e:
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, f"Error: {e}")
            self.status_label.configure(text="Ready to record")
            logger.error(f"Transcription failed: {e}")

def main():
    root = tk.Tk()
    app = WhisperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()