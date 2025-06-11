import whisper
import asyncio
from io import BytesIO
from typing import Optional, Dict, Any
import tempfile
import os

class VoiceService:
    def __init__(self):
        self.model = None

    async def initialize(self):
        """Load Whisper model"""
        if self.model is None:
            # Load the model asynchronously
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, whisper.load_model, "base"
            )

    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Transcribe audio to text using Whisper"""
        await self.initialize()

        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # Transcribe using Whisper
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.model.transcribe, temp_file_path
            )

            # Clean up temporary file
            os.unlink(temp_file_path)

            return {
                "text": result["text"].strip(),
                "language": result.get("language", "en"),
                "confidence": self._calculate_confidence(result),
                "success": True
            }

        except Exception as e:
            return {
                "text": "",
                "error": str(e),
                "success": False
            }

    def _calculate_confidence(self, whisper_result: Dict) -> float:
        """Calculate confidence score from Whisper result"""
        # Simplified confidence calculation
        segments = whisper_result.get("segments", [])
        if not segments:
            return 0.0

        avg_confidence = sum(seg.get("avg_logprob", 0) for seg in segments) / len(segments)
        return max(0.0, min(1.0, (avg_confidence + 1.0) / 2.0))  # Normalize to 0-1