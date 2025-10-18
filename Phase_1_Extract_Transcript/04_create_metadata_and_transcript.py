import json
import os
from pathlib import Path

"""
04_create_metadata_and_transcript.py

Goal: After steps 01 (transcribe), 02 (combine), and 03 (identify roles),
produce per-lesson JSON files that merge METADATA with the final
identified transcript.

Inputs (relative to Phase_1_Extract_Transcript/):
  - METADATA/metadata.json              # array of { title, sessionId, uploadedAt }
  - IDENTIFIED_TRANSCRIPTS/<sessionId>_identified.json

Output (Phase_1_Extract_Transcript/OUTPUT_LESSONS/):
  - <sessionId>.json with shape:
    {
      "sessionId": str,
      "title": str,
      "uploadedAt": str,
      "transcript": [ { speaker, start, end, text, role } ... ]
    }
"""

BASE = Path(__file__).resolve().parent
METADATA_FILE = BASE / 'METADATA' / 'metadata.json'
IDENTIFIED_DIR = BASE / 'IDENTIFIED_TRANSCRIPTS'
OUTPUT_DIR = BASE / 'OUTPUT_LESSONS'


def read_json(p: Path):
    with p.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def build_output_records():
    if not METADATA_FILE.exists():
        raise SystemExit(f"Missing METADATA file: {METADATA_FILE}")
    if not IDENTIFIED_DIR.exists():
        raise SystemExit(f"Missing IDENTIFIED_TRANSCRIPTS folder: {IDENTIFIED_DIR}")

    meta = read_json(METADATA_FILE)
    if not isinstance(meta, list):
        raise SystemExit("METADATA/metadata.json must be an array of objects")

    produced = []
    for m in meta:
        session_id = m.get('sessionId') or m.get('session_id')
        if not session_id:
            print("Skipping metadata entry without sessionId")
            continue

        id_path = IDENTIFIED_DIR / f"{session_id}_identified.json"
        if not id_path.exists():
            print(f"⚠️ Identified transcript missing for {session_id}: {id_path}")
            transcript = []
        else:
            try:
                transcript = read_json(id_path)
            except Exception as e:
                print(f"⚠️ Failed to read {id_path}: {e}")
                transcript = []

        record = {
            "sessionId": session_id,
            "title": m.get('title', ''),
            "uploadedAt": m.get('uploadedAt') or m.get('uploaded_at') or '',
            "transcript": transcript,
        }

        out_path = OUTPUT_DIR / f"{session_id}.json"
        write_json(out_path, record)
        produced.append(str(out_path))
        print(f"✅ Wrote {out_path}")

    return produced


def main():
    files = build_output_records()
    if not files:
        print("No outputs produced. Ensure METADATA and IDENTIFIED_TRANSCRIPTS are ready.")
    else:
        print(f"\n🏁 Done. {len(files)} lesson file(s) generated in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()


