import numpy as np
import queue
import sounddevice as sd
import threading
import time
from typing import Callable, Optional
from pathlib import Path
import tempfile
import wave
import os

class AudioManager:
    """Handles audio capture and processing with options for post-recording transcription."""
    
    def __init__(
        self, 
        sample_rate: int = 16000, 
        chunk_duration: float = 2.0,
        device: Optional[int] = None,
        record_dir: Optional[str] = None
    ):
        self.sample_rate = sample_rate
        self.channels = 1
        self.dtype = np.float32
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.overlap = int(sample_rate * 0.5)  # 0.5 second overlap
        self.device = device
        
        self.audio_queue = queue.Queue()
        self.stream = None
        self.is_running = False
        self.processing_thread = None
        
        # Buffer for continuous recording
        self.accumulated_audio = np.array([], dtype=self.dtype)
        
        # For full recordings
        self.recording_buffer = np.array([], dtype=self.dtype)
        self.is_recording = False
        self.record_dir = record_dir if record_dir else tempfile.gettempdir()
        self.current_recording_path = None
        
    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio stream"""
        if status:
            print(f"Audio status: {status}")
        audio_data = indata.copy()
        self.audio_queue.put(audio_data)
        
        # Also add to recording buffer if recording mode is active
        if self.is_recording:
            self.recording_buffer = np.append(self.recording_buffer, audio_data.flatten())
        
    def start(self, process_func: Optional[Callable[[np.ndarray], None]] = None):
        """Start audio capture and processing"""
        if self.is_running:
            return
            
        self.is_running = True
        self.accumulated_audio = np.array([], dtype=self.dtype)
        
        # Start processing thread if real-time processing is requested
        if process_func:
            self.processing_thread = threading.Thread(
                target=self._process_audio_thread,
                args=(process_func,),
                daemon=True
            )
            self.processing_thread.start()
        
        # Start audio stream
        self.stream = sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=self.dtype,
            callback=self.audio_callback,
            blocksize=int(self.sample_rate * 0.1),  # Process in 100ms chunks
            device=self.device
        )
        self.stream.start()
        
    def stop(self):
        """Stop audio capture and processing"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
                
        # Reset buffer
        self.accumulated_audio = np.array([], dtype=self.dtype)
        
    def _process_audio_thread(self, process_func: Callable[[np.ndarray], None]):
        """Thread function to process audio chunks (for real-time mode)"""
        while self.is_running:
            try:
                # Get audio chunk from queue with timeout
                audio_chunk = self.audio_queue.get(timeout=0.5).flatten()
                self.accumulated_audio = np.concatenate((self.accumulated_audio, audio_chunk))
                
                # Process when we have enough audio
                if len(self.accumulated_audio) >= self.chunk_size:
                    print(f"Processing audio chunk of length: {len(self.accumulated_audio)}")
                    
                    # Use a copy for processing
                    audio_to_process = self.accumulated_audio[:self.chunk_size].copy()
                    
                    # Check audio quality
                    max_val = np.max(np.abs(audio_to_process))
                    print(f"Audio max amplitude: {max_val:.4f}")
                    
                    # Send to callback function
                    try:
                        process_func(audio_to_process)
                    except Exception as e:
                        print(f"Error in audio processing: {e}")
                    
                    # Keep a small overlap
                    self.accumulated_audio = self.accumulated_audio[-self.overlap:] if len(self.accumulated_audio) > self.overlap else np.array([], dtype=self.dtype)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")
                
    def start_recording(self):
        """Start recording a full audio session"""
        print("Starting full audio recording...")
        self.recording_buffer = np.array([], dtype=self.dtype)
        self.is_recording = True
        
        # Make sure audio capture is active
        if not self.is_running:
            self.start(None)  # Start without real-time processing
        
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the buffer"""
        if not self.is_recording:
            return np.array([])
            
        print(f"Stopping recording... Captured {len(self.recording_buffer)} samples ({len(self.recording_buffer)/self.sample_rate:.2f}s)")
        self.is_recording = False
        return self.recording_buffer.copy()
    
    def get_recording(self) -> np.ndarray:
        """Get the current recording buffer without stopping recording"""
        return self.recording_buffer.copy()
    
    def save_recording(self, audio_data: Optional[np.ndarray] = None, filename: Optional[str] = None) -> str:
        """Save recording to WAV file"""
        if audio_data is None:
            audio_data = self.recording_buffer
            
        if len(audio_data) == 0:
            print("No audio data to save")
            return None
            
        # Generate filename if not provided
        if filename is None:
            timestamp = int(time.time())
            filename = f"recording_{timestamp}.wav"
            
        # Create full path
        filepath = os.path.join(self.record_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert float32 to int16 for WAV file
        int_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(int_data.tobytes())
            
        print(f"Recording saved to {filepath}")
        self.current_recording_path = filepath
        return filepath
    
    def list_devices(self):
        """List available audio devices"""
        return sd.query_devices()