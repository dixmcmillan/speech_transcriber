#!/usr/bin/env python3
import os
import sys
import time
import threading
import numpy as np
import queue
import argparse
from pathlib import Path
from typing import Optional
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller

from audio_manager import AudioManager
from transcriber import Transcriber
from text_output import TextOutput

# --- Configuration ---
MODEL_NAME = "small.en"
DEVICE = "cpu"
LANGUAGE = "en"
SAMPLE_RATE = 16000
RECORDING_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Transcriptions")

# Multiple toggle options - either the full Hyper+` combo, Hyper+1, or just F12
TOGGLE_COMBOS = [
    # Option 1: Hyper+` (original)
    {keyboard.Key.cmd, keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.shift, keyboard.KeyCode.from_char('`')},
    # Option 2: Just F12 for easier testing
    {keyboard.Key.f12},
]

class SpeechTranscriber:
    """Main application class for speech transcription."""
    
    def __init__(self):
        # State
        self.is_active = False
        self.is_running = True
        self.is_recording = False
        self.current_keys = set()
        
        # Create output directory
        os.makedirs(RECORDING_DIR, exist_ok=True)
        
        # Initialize components
        self.audio_manager = AudioManager(
            sample_rate=SAMPLE_RATE,
            record_dir=RECORDING_DIR
        )
        
        self.transcriber = Transcriber(
            model_name=MODEL_NAME,
            device=DEVICE,
            language=LANGUAGE
        )
        
        self.text_output = TextOutput()
        
        # Set up callback to send transcribed text to output
        self.transcriber.set_transcription_callback(self.text_output.type_text)
        
        # Keyboard listener
        self.keyboard_listener = None
        
    def start(self):
        """Start the application."""
        print("\n--- Speech Transcriber ---")
        print("IMPORTANT: This application requires microphone and accessibility permissions.")
        print("If this is your first run, please grant these permissions when prompted.")
        
        # Determine the terminal application
        import subprocess
        terminal_app = subprocess.check_output("ps -p $PPID -o comm=", shell=True).decode().strip()
        print(f"\nYou are running this script in: {terminal_app}")
        print(f"Please ensure that {terminal_app} has BOTH microphone and accessibility permissions in System Settings > Privacy & Security")
        
        # Test microphone access
        self._test_microphone()
        
        # Load the model
        self.transcriber.load_model()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
        
        print("\nSpeech Transcriber ready!")
        print("Recording mode: Post-recording (full audio)")
        print("First press of hotkey starts recording, second press stops and transcribes")
        print("Toggle options:")
        print("1. Hyper + ` (Command+Control+Option+Shift+`)")
        print("2. F12 key (added for easier testing)")
        print("Press Ctrl+C to exit completely")
        
        try:
            # Keep the main thread alive
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Clean up
            self.is_running = False
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            self.audio_manager.stop()
            self.transcriber.unload_model()
    
    def _test_microphone(self):
        """Test microphone access."""
        try:
            print("\nTesting microphone access...")
            devices = self.audio_manager.list_devices()
            print(f"Available audio devices: {len(devices)}")
            
            # Test the audio manager's start/stop
            print("Recording 1 second of audio to test permissions...")
            self.audio_manager.start(None)  # No processing function
            time.sleep(1)
            self.audio_manager.stop()
            print("Microphone test successful")
        except Exception as e:
            print(f"Error accessing microphone: {e}")
            print("Please grant microphone permissions to your Terminal application")
    
    def toggle(self):
        """Toggle recording/transcription on/off."""
        if self.is_recording:
            # Stop recording and transcribe
            print("\nStopping recording and starting transcription...")
            
            # Get recording data
            audio_data = self.audio_manager.stop_recording()
            
            if len(audio_data) > 0:
                audio_duration = len(audio_data) / SAMPLE_RATE
                print(f"Captured {audio_duration:.2f} seconds of audio")
                
                # Save the recording
                file_path = self.audio_manager.save_recording()
                
                # Transcribe the full recording
                result = self.transcriber.transcribe_full_recording(audio_data)
                
                # Stop the audio stream
                self.audio_manager.stop()
                
                # Reset state
                self.is_recording = False
                self.is_active = False
            else:
                print("No audio data captured")
                self.is_recording = False
                self.is_active = False
        else:
            # Start recording
            print("\nStarting recording... Speak into your microphone.")
            print("Press the same hotkey again to stop recording and transcribe.")
            
            # Start audio manager without real-time processing
            self.audio_manager.start(None)
            
            # Start recording
            self.audio_manager.start_recording()
            
            # Update state
            self.is_recording = True
            self.is_active = True
    
    def on_key_press(self, key):
        """Handle key press events for hotkey detection."""
        # print(f"Key pressed: {key}")  # Debug: Print every key press
        self.current_keys.add(key)
        
        # Check if any of our toggle combinations match
        for combo in TOGGLE_COMBOS:
            if self.current_keys.issuperset(combo):
                if not hasattr(self, 'last_toggle_time') or time.time() - self.last_toggle_time > 0.5:
                   # print(f"Toggle key combination detected! {combo}")
                    self.toggle()
                    # Debounce toggle to prevent double-activation
                    self.last_toggle_time = time.time()
                break
    
    def on_key_release(self, key):
        """Handle key release events."""
        try:

            self.current_keys.remove(key)
        except KeyError:
            pass

def transcribe_file(file_path, output_file=None, print_output=False):
    """
    Transcribe an audio file and save to file and/or print.
    
    Args:
        file_path: Path to the audio file to transcribe
        output_file: Path to save transcription as text file (auto-generated if None)
        print_output: Whether to print the transcription to terminal
    """
    print(f"\n--- Speech Transcriber - File Mode ---")
    print(f"Transcribing file: {file_path}")
    
    # Auto-generate output filename if not provided
    if output_file is None:
        audio_path = Path(file_path)
        output_file = str(audio_path.with_suffix('.txt'))
        print(f"Will save transcription to: {output_file}")
    else:
        print(f"Will save transcription to: {output_file}")
    
    # Initialize just the transcriber
    transcriber = Transcriber(
        model_name=MODEL_NAME,
        device=DEVICE,
        language=LANGUAGE
    )
    
    # Load the model
    transcriber.load_model()
    
    transcription_text = None
    
    # Callback to capture and optionally print the transcription
    def handle_transcription(text):
        nonlocal transcription_text
        transcription_text = text
        
        if print_output:
            print("\nTranscription:")
            print("-" * 40)
            print(text)
            print("-" * 40)
    
    # Set callback
    transcriber.set_transcription_callback(handle_transcription)
    
    try:
        # Transcribe the file
        result = transcriber.transcribe_file(file_path)
        if not result:
            print("Transcription failed.")
        elif transcription_text:
            # Save to text file
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(transcription_text)
                print(f"Transcription saved to: {output_file}")
            except Exception as e:
                print(f"Error saving transcription to file: {e}")
    finally:
        # Clean up
        transcriber.unload_model()

def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Speech Transcriber")
    parser.add_argument("--file", "-f", help="Path to audio file to transcribe")
    parser.add_argument("--output", "-o", help="Path to save transcription as text file")
    parser.add_argument("--print", "-p", action="store_true", help="Print the transcription to terminal")
    args = parser.parse_args()
    
    if args.file:
        # File transcription mode
        transcribe_file(args.file, args.output, args.print)
    else:
        # Real-time transcription mode
        transcriber = SpeechTranscriber()
        transcriber.start()

if __name__ == "__main__":
    main()
