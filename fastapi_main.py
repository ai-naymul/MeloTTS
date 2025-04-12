from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
from melo.api import TTS
import io
import logging
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
app = FastAPI()

# Initialize TTS models
models = {
    'EN': TTS(language='EN', device='auto'),
    'ES': TTS(language='ES', device='auto'),
    'FR': TTS(language='FR', device='auto'),
    'ZH': TTS(language='ZH', device='auto'),
    'JP': TTS(language='JP', device='auto'),
    'KR': TTS(language='KR', device='auto'),
}

class TTSRequest(BaseModel):
    text: str
    language: str = "EN"
    speaker: str = "EN-US"
    speed: float = 1.0

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    try:
        if request.language not in models:
            raise HTTPException(status_code=400, detail=f"Language {request.language} not supported")
        
        model = models[request.language]
        speaker_ids = model.hps.data.spk2id
        
        if request.language == 'EN':
            if request.speaker not in speaker_ids:
                request.speaker = 'EN-US'
            speaker_id = speaker_ids[request.speaker]
        else:
            speaker_id = speaker_ids[list(speaker_ids.keys())[0]]

        # Create a bytes buffer for the audio
        audio_buffer = io.BytesIO()
        
        # Generate audio
        model.tts_to_file(
            request.text,
            speaker_id,
            audio_buffer,
            speed=request.speed,
            format='wav'
        )
        
        # Reset buffer position
        audio_buffer.seek(0)
        
        return StreamingResponse(
            audio_buffer,
            media_type="audio/wav",
            headers={
                'Content-Disposition': 'attachment; filename="speech.wav"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in TTS synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))