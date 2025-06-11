from fastapi import FastAPI, UploadFile, File, Form, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio

from agents.main_agent import MainAgent
from services.voice_service import VoiceService
from services.cognee_service import CogneeService
from core.config import settings

app = FastAPI(title="FinMate Conversational AI", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
main_agent = MainAgent()
voice_service = VoiceService()
cognee_service = CogneeService()

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str

class FileUploadRequest(BaseModel):
    category: str
    description: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await voice_service.initialize()
    await cognee_service.initialize()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle text chat requests"""
    try:
        agent_request = {
            "type": "user_query",
            "query": request.message,
            "user_id": request.user_id,
            "session_id": request.session_id
        }

        response = await main_agent.process_request(agent_request)

        # Store conversation in database
        await cognee_service.store_conversation(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            response=response.get("response", "")
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...), 
                          user_id: str = Form(...),
                          session_id: str = Form(...)):
    """Handle voice input transcription"""
    try:
        audio_data = await audio.read()

        # Transcribe audio
        transcription = await voice_service.transcribe_audio(audio_data)

        if not transcription.get("success"):
            raise HTTPException(status_code=400, detail="Transcription failed")

        # Process the transcribed text as a chat message
        agent_request = {
            "type": "user_query",
            "query": transcription["text"],
            "user_id": user_id,
            "session_id": session_id
        }

        response = await main_agent.process_request(agent_request)

        return {
            "transcription": transcription["text"],
            "response": response.get("response", ""),
            "confidence": transcription.get("confidence", 0.0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/upload")
async def upload_file(file: UploadFile = File(...),
                     metadata: str = Form(...)):
    """Handle admin file uploads"""
    try:
        # Parse metadata
        file_metadata = json.loads(metadata)

        # Read file content
        content = await file.read()

        # Determine file type and process accordingly
        file_type = file.content_type

        agent_request = {
            "type": "file_upload",
            "file_data": content,
            "file_type": file_type,
            "filename": file.filename,
            "category": file_metadata.get("category", "general"),
            "description": file_metadata.get("description", "")
        }

        response = await main_agent.process_request(agent_request)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "chat":
                agent_request = {
                    "type": "user_query",
                    "query": data.get("message"),
                    "user_id": user_id,
                    "session_id": session_id
                }

                response = await main_agent.process_request(agent_request)

                # Send response back to client
                await websocket.send_json({
                    "type": "response",
                    "message": response.get("response", ""),
                    "agents_used": response.get("agents_used", [])
                })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FinMate API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)