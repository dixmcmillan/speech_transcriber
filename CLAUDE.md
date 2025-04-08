# Speech Transcriber Project Status

## Project Overview
We're building a real-time speech-to-text application with these features:
- Uses OpenAI Whisper model for local transcription
- Toggles on/off with a global hotkey (Hyper+`)
- Types text into the currently focused field
- Runs entirely locally with minimal resource usage

## Current Status
1. **Application Structure:**
   - Created modular design with main.py, audio_manager.py, transcriber.py, text_output.py
   - Added README.md, requirements.txt, and other support files
   - Application structure and code are in place

2. **Issues Being Addressed:**
   - **MPS Compatibility:** Fixed by forcing CPU for inference due to Whisper sparse tensor incompatibility with MPS
   - **Permissions:** Working on getting proper microphone and accessibility permissions for the terminal application

3. **Next Steps:**
   - Grant proper permissions to the terminal application running the script
   - Test audio input and keyboard output
   - Fine-tune performance and usability

## Important Implementation Details
- Using pynput for keyboard input simulation and hotkey detection
- Model is forced to use CPU to avoid MPS compatibility issues
- Audio is processed in ~2 second chunks with overlap for continuity
- Terminal application needs both microphone and accessibility permissions

## Debugging Status
- Added detailed logging throughout the application to trace:
  - Audio processing
  - Model inference
  - Transcription results
  - Keyboard output
  - Permission issues

## Command to Run
```bash
cd /Users/dixon/Documents/Code/whisper/speech_transcriber
python main.py
```

## Major Files
- `/Users/dixon/Documents/Code/whisper/speech_transcriber/main.py` - Main application logic and hotkey handling
- `/Users/dixon/Documents/Code/whisper/speech_transcriber/audio_manager.py` - Audio capture and processing
- `/Users/dixon/Documents/Code/whisper/speech_transcriber/transcriber.py` - Whisper model integration
- `/Users/dixon/Documents/Code/whisper/speech_transcriber/text_output.py` - Keyboard output handling