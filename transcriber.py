import numpy as np
import torch
import whisper
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Union

class Transcriber:
    """Handles transcription using the Whisper model."""
    
    def __init__(
        self,
        model_name: str = "small.en",
        device: str = "cpu",  # Force CPU by default for compatibility
        language: str = "en",
        compute_type: str = "float16",
        models_dir: Optional[str] = None
    ):
        self.model_name = model_name
        self.model = None
        self.language = language
        self.compute_type = compute_type
        self.device = self._get_device() if device is None else device
        self.models_dir = Path(models_dir) if models_dir else None
        
        # Callback for when transcription is ready
        self.transcription_callback = None
        
        # State variables
        self.is_loaded = False
        self.is_processing = False
        self.last_inference_time = 0
        
    def _get_device(self) -> str:
        """Determine optimal device for inference."""
        if torch.cuda.is_available():
            return "cuda"
        # MPS has compatibility issues with sparse tensors in Whisper
        # Always force CPU for now to avoid MPS errors
        return "cpu"
            
    def load_model(self):
        """Load Whisper model."""
        if self.is_loaded:
            return
            
        print(f"Loading Whisper model '{self.model_name}' on {self.device}...")
        load_start = time.time()
        
        # Set download directory if specified
        kwargs = {}
        if self.models_dir:
            kwargs["download_root"] = str(self.models_dir)
            
        # Load the model
        try:
            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                **kwargs
            )
            self.is_loaded = True
            load_time = time.time() - load_start
            print(f"Model loaded in {load_time:.2f}s")
        except Exception as e:
            print(f"Error loading model: {e}")
            
    def unload_model(self):
        """Unload model to free memory."""
        if not self.is_loaded:
            return
            
        self.model = None
        torch.cuda.empty_cache() if self.device == "cuda" else None
        self.is_loaded = False
        print("Model unloaded")
        
    def set_transcription_callback(self, callback: Callable[[str], None]):
        """Set callback for when transcription is ready."""
        self.transcription_callback = callback
        
    def transcribe(self, audio: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio data.
        
        Args:
            audio: Audio data as numpy array (float32, already normalized)
            
        Returns:
            Dictionary containing transcription result or None if error
        """
        if not self.is_loaded:
            self.load_model()
            
        if not self.is_loaded or self.is_processing:
            print("Model not loaded or already processing, skipping transcription")
            return None
            
        self.is_processing = True
        inference_start = time.time()
        
        try:
            print(f"Starting transcription of audio with shape {audio.shape}")
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                language=self.language,
                fp16=(self.compute_type == "float16" and self.device == "cuda")
            )
            
            inference_time = time.time() - inference_start
            self.last_inference_time = inference_time
            print(f"Transcription completed in {inference_time:.2f}s")
            print(f"Raw result: {result['text']}")
            
            # Call callback if provided
            if self.transcription_callback and result and "text" in result:
                text = result["text"].strip()
                if text:
                    print(f"Calling callback with: '{text}'")
                    self.transcription_callback(text)
                else:
                    print("Empty transcription result, not calling callback")
                
            return result
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.is_processing = False
    
    def transcribe_full_recording(self, audio: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Transcribe a full audio recording at once (optimized for longer segments).
        
        Args:
            audio: Complete audio recording as numpy array (float32)
            
        Returns:
            Dictionary containing transcription result or None if error
        """
        if not self.is_loaded:
            self.load_model()
            
        if not self.is_loaded or self.is_processing:
            print("Model not loaded or already processing, skipping transcription")
            return None
            
        self.is_processing = True
        inference_start = time.time()
        
        try:
            audio_duration = len(audio) / 16000  # Assuming 16kHz sample rate
            print(f"Starting transcription of full recording: {audio_duration:.2f} seconds")
            
            # Transcribe full recording at once
            result = self.model.transcribe(
                audio,
                language=self.language,
                fp16=(self.compute_type == "float16" and self.device == "cuda"),
                verbose=True  # Enable Whisper's progress display for long files
            )
            
            inference_time = time.time() - inference_start
            self.last_inference_time = inference_time
            
            print(f"Full transcription completed in {inference_time:.2f}s")
            if result and "text" in result:
                print(f"Transcription complete: {len(result['text'])} characters")
                
                # Call callback if provided
                if self.transcription_callback and result["text"].strip():
                    self.transcription_callback(result["text"].strip())
                
            return result
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.is_processing = False
            
    def transcribe_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Transcribe an audio file.
        
        Args:
            file_path: Path to audio file (WAV, MP3, etc.)
            
        Returns:
            Dictionary containing transcription result or None if error
        """
        if not self.is_loaded:
            self.load_model()
            
        if not self.is_loaded or self.is_processing:
            print("Model not loaded or already processing, skipping transcription")
            return None
            
        self.is_processing = True
        inference_start = time.time()
        
        try:
            file_path = str(file_path)
            print(f"Starting transcription of file: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None
                
            # Transcribe file 
            result = self.model.transcribe(
                file_path,
                language=self.language,
                fp16=(self.compute_type == "float16" and self.device == "cuda"),
                verbose=True
            )
            
            inference_time = time.time() - inference_start
            self.last_inference_time = inference_time
            
            print(f"File transcription completed in {inference_time:.2f}s")
            if result and "text" in result:
                print(f"Transcription complete: {len(result['text'])} characters")
                
                # Call callback if provided
                if self.transcription_callback and result["text"].strip():
                    self.transcription_callback(result["text"].strip())
                
            return result
        except Exception as e:
            print(f"File transcription error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.is_processing = False
            
    def process_audio(self, audio: np.ndarray):
        """Process audio chunk and handle transcription."""
        # Convert to float32 normalized between -1 and 1
        if audio.dtype != np.float32:
            float_data = audio.astype(np.float32)
        else:
            float_data = audio
            
        # Ensure audio is properly normalized
        if float_data.max() > 1.0 or float_data.min() < -1.0:
            float_data = np.clip(float_data / max(abs(float_data.max()), abs(float_data.min())), -1.0, 1.0)
            
        # Transcribe
        return self.transcribe(float_data)