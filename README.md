# Whisper CLI

A command-line tool for recording and transcribing audio using OpenAI's Whisper model.

## Setup

1. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Make sure your virtual environment is activated
2. Run the script:
```bash
python whisper_cli.py
```
3. Press SPACE to stop recording
4. The transcription will be copied to your clipboard and displayed in the console

## Features

- Real-time audio recording
- Automatic transcription using Whisper
- Clipboard integration
- Progress feedback and logging 