import whisper

# Function that receives an audio file, and returns a string of the transcripted audio
def transcribe_audio(audio_file):
    # Load Whisper model
    model = whisper.load_model("base")
    
    # Transcribe audio file
    result = model.transcribe(audio_file)

    return result["text"]

if __name__ == "__main__":
    # Test the function
    audio_file = "record.m4a"
    print(transcribe_audio(audio_file))