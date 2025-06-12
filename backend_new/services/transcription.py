"""
Transcription Service for converting audio to text.

This service provides interfaces for transcribing audio files and voice input
to text using speech recognition models.
"""
import os
import base64
import logging
import tempfile
from typing import Dict, Any, Optional, BinaryIO, Union
from pathlib import Path
import whisper
import numpy as np
import tempfile

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing audio to text."""
    
    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize the transcription service.
        
        Args:
            model_name: Name of the Whisper model to use (tiny, base, small, medium, large)
            device: Device to use for inference (cpu, cuda)
            compute_type: Compute type (float16, float32, int8)
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    @property
    def model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                logger.info(f"Loading Whisper model '{self.model_name}' on {self.device}")
                self._model = whisper.load_model(self.model_name, device=self.device)
                logger.info(f"Successfully loaded Whisper model")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {str(e)}")
                raise
        return self._model
    
    async def transcribe_file(self, audio_file: BinaryIO, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_file: Audio file handle
            language: Optional language code (e.g., "en", "es")
            
        Returns:
            Dict[str, Any]: Transcription result
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                audio_file.seek(0)
                temp_file.write(audio_file.read())
            
            # Process with Whisper
            logger.info(f"Transcribing audio file using Whisper")
            
            transcribe_options = {}
            if language:
                transcribe_options["language"] = language
            
            result = self.model.transcribe(temp_path, **transcribe_options)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Parse result
            text = result["text"].strip()
            segments = [
                {
                    "id": i,
                    "text": seg["text"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "confidence": seg.get("confidence", 0.0)
                }
                for i, seg in enumerate(result.get("segments", []))
            ]
            
            return {
                "text": text,
                "segments": segments,
                "language": result.get("language"),
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio file: {str(e)}")
            return {"error": str(e), "text": "", "segments": []}
    
    async def transcribe_base64(self, audio_base64: str, file_format: str = "wav") -> Dict[str, Any]:
        """
        Transcribe base64-encoded audio to text.
        
        Args:
            audio_base64: Base64-encoded audio data
            file_format: Audio file format (wav, mp3, etc.)
            
        Returns:
            Dict[str, Any]: Transcription result
        """
        try:
            # Decode base64 data
            audio_data = base64.b64decode(audio_base64)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)
            
            # Process with Whisper
            logger.info(f"Transcribing base64 audio using Whisper")
            result = self.model.transcribe(temp_path)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Parse result
            text = result["text"].strip()
            
            return {
                "text": text,
                "language": result.get("language"),
            }
            
        except Exception as e:
            logger.error(f"Error transcribing base64 audio: {str(e)}")
            return {"error": str(e), "text": ""}
    
    async def detect_language(self, audio_file: BinaryIO) -> str:
        """
        Detect the language of an audio file.
        
        Args:
            audio_file: Audio file handle
            
        Returns:
            str: Detected language code
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                audio_file.seek(0)
                temp_file.write(audio_file.read())
            
            # Process with Whisper
            logger.info(f"Detecting language using Whisper")
            
            # Use the first 30 seconds for language detection
            audio = whisper.load_audio(temp_path)
            audio = whisper.pad_or_trim(audio)
            
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Get the language with highest probability
            language = max(probs, key=probs.get)
            probability = probs[language]
            
            return {
                "language": language,
                "probability": probability,
            }
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return {"error": str(e), "language": "en", "probability": 0.0} 