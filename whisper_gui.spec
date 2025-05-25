# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Get the path to the whisper package
import whisper
import os
whisper_path = os.path.dirname(whisper.__file__)

a = Analysis(
    ['whisper_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons', 'icons'),  # Include icons directory
        (os.path.join(whisper_path, 'assets'), 'whisper/assets'),  # Include whisper assets
    ],
    hiddenimports=[
        'PIL._tkinter_finder',  # Required for PIL/Tkinter integration
        'numpy',
        'sounddevice',
        'whisper',
        'sounddevice._portaudio',  # Required for sounddevice
        'numpy.core._methods',
        'numpy.lib.format',
        'torch',
        'torchaudio',
        'torchaudio.transforms',
        'torchaudio.functional',
        'torchaudio.models',
        'torchaudio.datasets',
        'torchaudio.pipelines',
        'torchaudio.sox_effects',
        'torchaudio.utils',
        'torchaudio.backend',
        'torchaudio.backend.utils',
        'torchaudio.backend.sox',
        'torchaudio.backend.no_backend',
        'torchaudio.backend.soundfile',
        'torchaudio.backend.utils',
        'torchaudio.backend.sox_io',
        'torchaudio.backend.sox_effects',
        'torchaudio.backend.sox_utils',
        'torchaudio.backend.sox_io_backend',
        'torchaudio.backend.sox_effects_backend',
        'torchaudio.backend.sox_utils_backend',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add PortAudio DLLs
import sounddevice
portaudio_path = os.path.dirname(sounddevice.__file__)
a.binaries += [
    ('libportaudio-2.dll', os.path.join(portaudio_path, 'libportaudio-2.dll'), 'BINARY'),
]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhisperGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/mic.ico',  # Set the application icon
)
