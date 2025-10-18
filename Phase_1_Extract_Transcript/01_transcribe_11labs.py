import os
import subprocess
from io import BytesIO
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import json

# ----------------------------
# 1️⃣ Setup
# ----------------------------
load_dotenv()
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_KEY:
    raise EnvironmentError("Please set ELEVENLABS_API_KEY in your .env file")

eleven = ElevenLabs(api_key=ELEVEN_KEY)

# Always resolve paths relative to this script's folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_FOLDER = os.path.join(BASE_DIR, "VIDEOS")
AUDIO_FOLDER = os.path.join(BASE_DIR, "AUDIO_OUT")
TRANSCRIPT_FOLDER = os.path.join(BASE_DIR, "TRANSCRIPTS")
METADATA_FILE = os.path.join(BASE_DIR, "METADATA/metadata.json")

# Create folders if not exist
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

# Load optional metadata mapping: videoTitle -> sessionId
metadata_map = {}
try:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
        if isinstance(items, list):
            for it in items:
                # Map videoTitle (filename without extension) to sessionId
                video_title = (it.get("videoTitle") or "").strip()
                sid = it.get("sessionId") or it.get("session_id")
                if video_title and sid:
                    metadata_map[video_title] = sid
except Exception as e:
    print(f"⚠️ Failed to read METADATA file: {e}")


# ----------------------------
# 2️⃣ MP4 → MP3 conversion
# ----------------------------
def convert_to_mp3(video_file, output_file):
    """Converts a video file into MP3 format using ffmpeg."""
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video not found: {video_file}")
    cmd = [
        "ffmpeg", "-i", video_file,
        "-vn",            # no video
        "-acodec", "libmp3lame",
        "-ab", "192k",
        "-ar", "44100",
        output_file,
        "-y"              # overwrite
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Converted to {output_file}")


# ----------------------------
# 3️⃣ Transcription
# ----------------------------
def transcribe_audio(file_path):
    """Transcribes the given MP3 file using ElevenLabs Scribe v1."""
    with open(file_path, "rb") as f:
        audio_bytes = BytesIO(f.read())

    print(f"⏳ Uploading {file_path} to ElevenLabs...")
    result = eleven.speech_to_text.convert(
        file=audio_bytes,
        model_id="scribe_v1",
        diarize=True,
        tag_audio_events=True,
        language_code="eng",
        timestamps_granularity="word"  # segment-level
    )
    print(f"✅ Transcription complete for {file_path}")
    return result


# ----------------------------
# 4️⃣ Process all videos
# ----------------------------
def process_all_videos():
    video_files = [
        f for f in os.listdir(VIDEO_FOLDER)
        if f.lower().endswith(".mp4")
    ]

    if not video_files:
        print("⚠️ No MP4 files found in VIDEOS folder.")
        return

    for video_name in video_files:
        video_path = os.path.join(VIDEO_FOLDER, video_name)
        audio_path = os.path.join(AUDIO_FOLDER, video_name.replace(".mp4", ".mp3"))
        title = os.path.splitext(video_name)[0]
        session_id = metadata_map.get(title)
        transcript_filename = (f"{session_id}_transcript.json" if session_id else video_name.replace(".mp4", "_transcript.json"))
        transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)

        print(f"\n🎬 Processing: {video_name}")

        # Step 1: Convert to MP3
        convert_to_mp3(video_path, audio_path)

        # Step 2: Transcribe
        transcription = transcribe_audio(audio_path)

        # Step 3: Convert to dict and save
        if hasattr(transcription, "model_dump"):
            transcription_data = transcription.model_dump()
        elif isinstance(transcription, list):
            transcription_data = [t.model_dump() for t in transcription]
        else:
            transcription_data = json.loads(str(transcription))

        with open(transcript_path, "w", encoding="utf-8") as out:
            json.dump(transcription_data, out, indent=2, ensure_ascii=False)

        print(f"💾 Transcript saved at {transcript_path}")


# ----------------------------
# 5️⃣ Main entry
# ----------------------------
if __name__ == "__main__":
    process_all_videos()
    print("\n🏁 All videos processed successfully!")