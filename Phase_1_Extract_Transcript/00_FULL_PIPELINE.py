import subprocess
import sys
from pathlib import Path

"""
Run the full Phase 1 pipeline in order:
  1) 01_transcribe_11labs.py        -> writes TRANSCRIPTS/<sessionId>_transcript.json
  2) 02_combine_speech_segments.py   -> writes COMBINED_TRANSCRIPTS/<sessionId>_combined.json
  3) 03_teacher_student_tagging.py   -> writes IDENTIFIED_TRANSCRIPTS/<sessionId>_identified.json
  4) 04_create_metadata_and_transcript.py -> writes OUTPUT_LESSONS/<sessionId>.json
  5) 05_evaluate.py                  -> writes OUTPUT_ANALYSIS/<sessionId>_analysis.md, updates OUTPUT_LESSONS
  6) 06_push_to_supabase.py          -> pushes to Supabase lessons table
  7) 07_send_email.py                -> sends email feedback to teacher
  
Phase 3: Pedagogy Analysis
  8) 08_extract_question_context.py  -> writes OUTPUT_QUESTION_CONTEXT/<sessionId>_context.json
  9) 09_classify_patterns.py         -> writes OUTPUT_PATTERNS/<sessionId>_patterns.json
 10) 10_analyze_pedagogy.py          -> writes OUTPUT_PEDAGOGY_ANALYSIS/<sessionId>_pedagogy.json (Anthropic API)
 11) 11_push_pedagogy_to_supabase.py -> updates Supabase lessons.pedagogy_analysis column

Usage:
  python3 00_FULL_PIPELINE.py
"""

BASE = Path(__file__).resolve().parent

def run(script: str):
    print(f"\n▶️ Running {script}...")
    proc = subprocess.run([sys.executable, str(BASE / script)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(f"❌ {script} failed with exit code {proc.returncode}")
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    print(f"✅ {script} completed")


def main():
    # Phase 1: Transcript Processing & Analysis
    run('01_transcribe_11labs.py')
    run('02_combine_speech_segments.py')
    run('03_teacher_student_tagging.py')
    run('04_create_metadata_and_transcript.py')
    run('05_evaluate.py')
    run('06_push_to_supabase.py')
    run('07_send_email.py')
    
    # Phase 3: Pedagogy Analysis
    print("\n" + "="*60)
    print("PHASE 3: PEDAGOGY ANALYSIS")
    print("="*60)
    run('08_extract_question_context.py')
    run('09_classify_patterns.py')
    run('10_analyze_pedagogy.py')
    run('11_push_pedagogy_to_supabase.py')
    
    print("\n🏁 Full pipeline finished successfully!")
    print("   ✅ Transcripts processed and analyzed")
    print("   ✅ Teaching feedback sent via email")
    print("   ✅ Pedagogy analysis completed and pushed to Supabase")


if __name__ == '__main__':
    main()


