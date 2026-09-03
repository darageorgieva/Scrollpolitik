import whisper
from pathlib import Path

current_dir = Path(__file__).resolve().parent
audio_file_path = current_dir.parent / "data/mp3/kicklherbert_7409992801452182817.mp3"

model = whisper.load_model("turbo")
result = model.transcribe(str(audio_file_path))
print(result["text"])