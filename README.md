# speech-to-insight
import whisper

# Load Whisper model
model = whisper.load_model("base")

# Transcribe audio file
result = model.transcribe("audio.mp4")
print("Transcribed Text:", result["text"])