import os
import assemblyai as aai
from deepgram import DeepgramClient
import httpx

class TranscriptionService:
    def transcribe(self, filepath):
        raise NotImplementedError

class AssemblyAIService(TranscriptionService):
    def __init__(self, api_key):
        aai.settings.api_key = api_key
        self.transcriber = aai.Transcriber()

    def transcribe(self, filepath):
        try:
            config = aai.TranscriptionConfig(
                speech_models=["universal-3-pro"],
                language_code="pt", 
                speaker_labels=True,
                domain="medical-v1"
            )
            transcript = self.transcriber.transcribe(filepath, config=config)
            
            if transcript.status == aai.TranscriptStatus.error:
                return f"Erro: {transcript.error}"
                
            text = ""
            if hasattr(transcript, 'utterances') and transcript.utterances:
                for turn in transcript.utterances:
                    text += f"Speaker {turn.speaker}: {turn.text}\n\n"
            else:
                text = transcript.text
                
            return text
        except Exception as e:
            return f"Erro AssemblyAI: {str(e)}"

class DeepgramService(TranscriptionService):
    def __init__(self, api_key):
        self.api_key = api_key
        # Timeout settings for large files
        timeout_config = httpx.Timeout(
            timeout=600.0, 
            connect=30.0, 
            read=600.0, 
            write=900.0
        )
        self.client = DeepgramClient(api_key=api_key, timeout=timeout_config)

    def transcribe(self, filepath):
        try:
            with open(filepath, "rb") as file:
                buffer_data = file.read()
            
            options = {
                "model": "nova-3",
                "smart_format": True,
                "diarize": True,
                "paragraphs": True,
                "language": "pt-BR",
            }
            
            # Use explicit keyword arguments to avoid any positional argument confusion
            # The SDK v6.0.0 (Fern-generated) expects everything as keyword arguments
            response = self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model=options.get("model", "nova-3"),
                language=options.get("language", "pt-BR"),
                smart_format=options.get("smart_format", True),
                diarize=options.get("diarize", True),
                paragraphs=options.get("paragraphs", True)
            )
            
            # Format Diarization
            text = ""
            paragraphs = response.results.channels[0].alternatives[0].paragraphs
            
            if paragraphs and hasattr(paragraphs, 'paragraphs'):
                for para in paragraphs.paragraphs:
                    speaker = para.speaker
                    content = " ".join([s.text for s in para.sentences])
                    text += f"Speaker {speaker}: {content}\n\n"
            else:
                text = response.results.channels[0].alternatives[0].transcript
                
            return text

        except Exception as e:
            error_text = str(e)
            if "INVALID_AUTH" in error_text or "Invalid credentials" in error_text or "status_code: 401" in error_text:
                return (
                    "Erro Deepgram: credenciais invalidas. "
                    "Defina uma chave valida em DEEPGRAM_API_KEY no arquivo .env e reinicie o aplicativo."
                )
            return f"Erro Deepgram: {error_text}"
