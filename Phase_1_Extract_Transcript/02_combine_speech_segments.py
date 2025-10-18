import json
import os

# ------------------------------
# SETTINGS
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_FOLDER = os.path.join(BASE_DIR, "TRANSCRIPTS")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "COMBINED_TRANSCRIPTS")
PAUSE_THRESHOLD = 2.0  # seconds

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ------------------------------
# MAIN FUNCTION
# ------------------------------
def combine_by_speaker_turns(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Try to find the "segments" or "words" list in ElevenLabs output
    segments = []
    if isinstance(data, list):
        for chunk in data:
            if isinstance(chunk, dict):
                segments.extend(chunk.get("segments", []))
    elif isinstance(data, dict):
        segments = data.get("segments", [])
    else:
        raise ValueError("Unsupported JSON structure")

    # Fall back to words list if no segments
    if not segments and isinstance(data, dict):
        segments = data.get("words", [])

    if not segments:
        print(f"⚠️ No segments found in {json_path}")
        return []

    # Normalize structure
    clean = []
    for s in segments:
        text = s.get("text", "").strip()
        start = float(s.get("start", 0.0))
        end = float(s.get("end", start))
        speaker = s.get("speaker") or s.get("speaker_id") or "Unknown"
        if text:
            clean.append({"speaker": speaker, "text": text, "start": start, "end": end})

    # Sort by time
    clean.sort(key=lambda x: x["start"])

    # Combine by speaker turns with pause > 2s
    combined = []
    if not clean:
        return combined

    current_speaker = clean[0]["speaker"]
    current_text = clean[0]["text"]
    current_start = clean[0]["start"]
    current_end = clean[0]["end"]

    for seg in clean[1:]:
        speaker = seg["speaker"]
        start, end, text = seg["start"], seg["end"], seg["text"]

        if (
            speaker == current_speaker
            and (start - current_end) <= PAUSE_THRESHOLD
        ):
            # Same speaker, short pause — continue same turn
            current_text += " " + text
            current_end = end
        else:
            # Different speaker or long pause — save current, start new
            combined.append({
                "speaker": current_speaker,
                "start": current_start,
                "end": current_end,
                "text": current_text.strip()
            })
            current_speaker = speaker
            current_start = start
            current_end = end
            current_text = text

    # Save last entry
    combined.append({
        "speaker": current_speaker,
        "start": current_start,
        "end": current_end,
        "text": current_text.strip()
    })

    return combined


# ------------------------------
# PROCESS ALL TRANSCRIPTS
# ------------------------------
def process_all_transcripts():
    files = [f for f in os.listdir(TRANSCRIPTS_FOLDER) if f.endswith("_transcript.json")]
    if not files:
        print("⚠️ No transcript JSON files found.")
        return

    for f in files:
        in_path = os.path.join(TRANSCRIPTS_FOLDER, f)
        out_path = os.path.join(OUTPUT_FOLDER, f.replace("_transcript.json", "_combined.json"))

        print(f"🧩 Processing {f}...")
        combined = combine_by_speaker_turns(in_path)

        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(combined, out, indent=2, ensure_ascii=False)

        print(f"✅ Combined transcript saved at {out_path} ({len(combined)} entries)")


if __name__ == "__main__":
    process_all_transcripts()
    print("\n🏁 All transcripts combined successfully!")