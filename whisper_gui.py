import sounddevice as sd
import numpy as np
import whisper
import win32clipboard
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import time
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running as PyInstaller exe, use the current directory
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def get_icon_path(icon_name):
    """Get the path to an icon, trying both .ico and .png extensions"""
    # First try the icons directory
    icon_dir = get_resource_path('icons')
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
        logger.info(f"Created icons directory: {icon_dir}")
    
    # Try .ico first
    ico_path = os.path.join(icon_dir, f"{icon_name}.ico")
    if os.path.exists(ico_path):
        return ico_path
    
    # Then try .png
    png_path = os.path.join(icon_dir, f"{icon_name}.png")
    if os.path.exists(png_path):
        return png_path
    
    # If neither exists, return None
    logger.warning(f"Icon not found: {icon_name}")
    return None

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
        
        # Initialize audio device
        try:
            devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')
            logger.info(f"Available audio devices: {devices}")
            logger.info(f"Default input device: {default_input}")
        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
            raise

    def load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # First try to load the model directly
            try:
                self.model = whisper.load_model(self.model_name)
                logger.info("Model loaded successfully.")
                return
            except Exception as e:
                logger.warning(f"Initial model load failed: {e}")
            
            # If direct load fails, try to find assets in different locations
            possible_paths = []
            
            # 1. Try PyInstaller path
            try:
                base_path = sys._MEIPASS
                possible_paths.append(os.path.join(base_path, 'whisper', 'assets'))
            except Exception:
                pass
            
            # 2. Try current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths.append(os.path.join(current_dir, 'whisper', 'assets'))
            
            # 3. Try site-packages
            import site
            for site_dir in site.getsitepackages():
                possible_paths.append(os.path.join(site_dir, 'whisper', 'assets'))
            
            # Log all paths we're checking
            logger.info("Checking for Whisper assets in:")
            for path in possible_paths:
                logger.info(f"  - {path}")
            
            # Try to find the assets
            assets_found = False
            for assets_path in possible_paths:
                if os.path.exists(assets_path):
                    logger.info(f"Found Whisper assets at: {assets_path}")
                    # Set the environment variable for Whisper
                    os.environ['WHISPER_ASSETS'] = assets_path
                    assets_found = True
                    break
            
            if not assets_found:
                logger.error("Whisper assets not found in any location")
                raise FileNotFoundError("Whisper assets not found")
            
            # Try loading the model again
            self.model = whisper.load_model(self.model_name)
            logger.info("Model loaded successfully after setting assets path.")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def callback(self, indata, frames, time, status):
        """Callback function for sounddevice stream"""
        if status:
            logger.warning(f"Audio stream status: {status}")
        try:
            self.BUFFER.append(indata.copy())
            # Calculate audio level (RMS)
            self.audio_level = np.sqrt(np.mean(indata**2))
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")

    def start_recording(self):
        """Start recording audio"""
        try:
            # Test audio device before starting
            test_stream = sd.InputStream(samplerate=self.SAMPLE_RATE, channels=self.CHANNELS, dtype='float32')
            test_stream.close()
            
            self.stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype='float32',
                callback=self.callback,
                blocksize=1024
            )
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

        try:
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
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None

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
        
        # Set window/taskbar icon
        try:
            icon_path = get_icon_path('mic')
            if icon_path:
                self.root.iconbitmap(icon_path)
                logger.info(f"Set window icon: {icon_path}")
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
        
        # Configure root window background
        self.root.configure(bg='#2b2b2b')
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window position
        window_width = 1200
        window_height = 150
        x_position = (screen_width - window_width) // 2  # Center horizontally
        y_position = screen_height // 5  # First fifth from top
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Prevent window from being resized
        self.root.resizable(False, False)

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
        
        # Update window to ensure proper rendering
        self.root.update_idletasks()
        
        # Ensure window stays on top initially
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

    def load_icons(self):
        """Load and prepare icons for the application"""
        try:
            # Initialize icons dictionary
            self.icons = {}

            # Load record button icon
            record_path = get_icon_path('record')
            if record_path:
                record_img = Image.open(record_path)
                record_img = record_img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icons['record'] = ImageTk.PhotoImage(record_img)
                logger.info("Record button loaded successfully")
            else:
                logger.error("Record button not found")

            # Load microphone icon
            mic_path = get_icon_path('mic')
            if mic_path:
                mic_img = Image.open(mic_path)
                mic_img = mic_img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icons['mic'] = ImageTk.PhotoImage(mic_img)
                logger.info("Microphone icon loaded successfully")
            else:
                logger.error("Microphone icon not found")

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

        # Main frame with dark background
        main_frame = ttk.Frame(self.root, padding="5", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top frame for button, status and visualizer
        top_frame = ttk.Frame(main_frame, style="TFrame")
        top_frame.pack(fill=tk.X, pady=5)

        # Left frame for button and status
        left_frame = ttk.Frame(top_frame, style="TFrame")
        left_frame.pack(side=tk.LEFT, padx=5)

        # Record button with icon
        self.record_button = ttk.Button(
            left_frame,
            text="🔴",  # Fallback emoji
            width=3,
            command=self.toggle_recording,
            style="TButton"
        )
        if self.icons.get('record'):
            self.record_button.configure(image=self.icons['record'])
        self.record_button.pack(side=tk.LEFT)

        # Status label
        self.status_label = ttk.Label(
            left_frame,
            text="Ready to record",
            font=("Segoe UI", 10),
            foreground='white',
            style="TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Visualizer frame (to the right of the button and status)
        self.visualizer_frame = ttk.Frame(top_frame, style="TFrame")
        self.visualizer_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create visualizer bars
        self.bars = []
        for i in range(40):  # Increased number of bars for wider window
            bar = tk.Canvas(
                self.visualizer_frame,
                width=10,
                height=20,
                bg='#2b2b2b',
                highlightthickness=0
            )
            bar.pack(side=tk.LEFT, padx=1)
            self.bars.append(bar)
        
        # Hide visualizer initially
        self.visualizer_frame.pack_forget()

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
        
        # Update the window to ensure proper rendering
        self.root.update_idletasks()

    def update_visualizer(self):
        """Update the visualizer bars based on audio level"""
        if not self.recorder.is_recording:
            return

        # Get current audio level and scale it
        level = min(1.0, self.recorder.audio_level * 5)  # Scale up the level for better visibility
        
        # Update each bar
        for i, bar in enumerate(self.bars):
            # Calculate bar height based on level and position
            bar_height = int(20 * level * (1 - abs(i - 20) / 20))
            bar_height = max(2, bar_height)  # Minimum height of 2 pixels
            
            # Clear previous bar
            bar.delete("all")
            
            # Draw new bar
            bar.create_rectangle(
                0, 20 - bar_height,
                10, 20,
                fill='#ff4444' if level > 0.5 else '#ff8888',
                outline=''
            )

        # Schedule next update
        self.root.after(50, self.update_visualizer)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.record_button.configure(image=self.icons['mic'])
        self.status_label.configure(text="Recording...")
        self.visualizer_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.update_visualizer()
        threading.Thread(target=self._record, daemon=True).start()

    def _record(self):
        try:
            self.recorder.start_recording()
        except Exception as e:
            error_msg = f"Error starting recording: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Recording Error", error_msg))
            self.record_button.configure(image=self.icons['record'])
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, error_msg)

    def stop_recording(self):
        self.record_button.configure(image=self.icons['record'])
        self.status_label.configure(text="Generating text...")
        self.visualizer_frame.pack_forget()
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
            error_msg = f"Error during transcription: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Transcription Error", error_msg))
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, error_msg)
            self.status_label.configure(text="Ready to record")

def main():
    root = tk.Tk()
    app = WhisperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()