# Speech Transcriber

A resource-efficient speech-to-text application that transcribes your speech and types it wherever your cursor is focused. Built with OpenAI's Whisper and optimized for macOS.

## Features

- **Post-recording transcription** for maximum accuracy
- **Global hotkey toggle** - press Hyper+` (Cmd+Ctrl+Option+Shift+`) to start/stop recording
- **Resource efficient** - loads/unloads components as needed
- **Self-contained** - runs entirely on your local machine
- **Saves recordings** - automatically saves audio files for reference

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd speech_transcriber
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Press any of the following hotkeys to start recording:
   - **Hyper+`** (Cmd+Ctrl+Option+Shift+`)
   - **Hyper+1** (Cmd+Ctrl+Option+Shift+1)
   - **F12**
   - **Ctrl+F12**

3. Speak into your microphone.

4. Press the same hotkey again to stop recording and transcribe.

5. The transcribed text will be typed wherever your cursor is focused.

6. Press **Ctrl+C** in the terminal to exit the application completely.

## Requirements

- Python 3.8 or higher
- macOS
- Microphone access
- Accessibility permissions for keyboard simulation

## Technical Notes

- The application uses CPU for inference due to compatibility issues with MPS (Metal) backend and sparse tensors in Whisper.
- Recordings are saved to `~/Documents/Transcriptions/` by default.
- The first run will download the Whisper model (~461MB for small.en).

## Permissions

This application requires:
1. **Microphone access** - to capture your speech
2. **Accessibility permissions** - to simulate keyboard input

When running for the first time, you may need to grant these permissions in System Settings > Privacy & Security.

## Advanced Configuration

You can modify the behavior by editing the parameters in `main.py`:

- Change the model size (`tiny.en`, `base.en`, `small.en`, `medium.en`, `large`)
- Adjust audio parameters for different quality/size tradeoffs
- Configure different hotkeys
- Change the recording directory

## Troubleshooting

If you encounter issues:
1. Ensure your microphone is properly connected and has permissions
2. Check terminal output for error messages
3. Try restarting the application
4. Make sure you've granted Accessibility permissions to your terminal application

## Comparison to Streaming Mode

The post-recording transcription mode:
- Provides higher accuracy for complete phrases and sentences
- Allows Whisper to process the entire audio at once for better context
- Reduces issues with hotkey detection and termination
- Creates a permanent record of recordings for reference
- Trades real-time feedback for improved quality