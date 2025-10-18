import os
import json
import math
from collections import defaultdict

# -------------------------------
# SETTINGS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of this script
TRANSCRIPTS_FOLDER = os.path.join(BASE_DIR, "COMBINED_TRANSCRIPTS")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "IDENTIFIED_TRANSCRIPTS")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -------------------------------
# FUNCTION TO IDENTIFY TEACHER
# -------------------------------
def identify_teacher(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Expect a list of {speaker, start, end, text}
    if not isinstance(data, list):
        print(f"⚠️ Invalid JSON structure in {json_path}")
        return None

    # 🧹 Round down start/end to whole integers; guarantee end >= start
    for seg in data:
        try:
            s = int(math.floor(float(seg.get("start", 0.0))))
        except Exception:
            s = 0
        try:
            e_raw = seg.get("end", s)
            e = int(math.floor(float(e_raw)))
        except Exception:
            e = s
        if e < s:
            e = s
        seg["start"] = s
        seg["end"] = e

    # Calculate total speaking time per speaker (using floored times)
    durations = defaultdict(float)
    counts = defaultdict(int)
    for seg in data:
        start = seg["start"]  # already int
        end = seg["end"]      # already int
        spk = seg.get("speaker", "Unknown")
        durations[spk] += max(0.0, end - start)
        counts[spk] += 1

    if not durations:
        print(f"⚠️ No valid segments found in {json_path}")
        return None

    # Sort speakers by total speaking time (descending)
    sorted_speakers = sorted(durations.items(), key=lambda x: x[1], reverse=True)
    teacher, teacher_time = sorted_speakers[0]

    # Print summary table
    print(f"\n🎬 File: {os.path.basename(json_path)}")
    print("─────────────────────────────────────────────")
    print(f"{'Speaker':<15} {'Segments':<10} {'Total Time (s)':<15}")
    print("─────────────────────────────────────────────")
    for spk, total_time in sorted_speakers:
        print(f"{spk:<15} {counts[spk]:<10} {total_time:<15.0f}")
    print("─────────────────────────────────────────────")
    print(f"🎓 Identified TEACHER: {teacher} ({teacher_time:.0f} s total)\n")

    # Add role field
    updated = []
    for seg in data:
        seg_copy = seg.copy()
        seg_copy["role"] = "TEACHER" if seg_copy.get("speaker") == teacher else "STUDENT"
        updated.append(seg_copy)

    return teacher, updated


# -------------------------------
# PROCESS ALL FILES
# -------------------------------
def process_all_files():
    files = [f for f in os.listdir(TRANSCRIPTS_FOLDER) if f.endswith("_combined.json")]
    if not files:
        print("⚠️ No combined transcripts found.")
        return

    for f in files:
        in_path = os.path.join(TRANSCRIPTS_FOLDER, f)
        out_path = os.path.join(OUTPUT_FOLDER, f.replace("_combined.json", "_identified.json"))

        result = identify_teacher(in_path)
        if result:
            _, updated_data = result
            with open(out_path, "w", encoding="utf-8") as out:
                json.dump(updated_data, out, indent=2, ensure_ascii=False, separators=(",", ": "))
            print(f"✅ Saved with TEACHER label (integer start/end) at {out_path}")


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    process_all_files()
    print("\n🏁 Teacher identification + integer start/end complete!")