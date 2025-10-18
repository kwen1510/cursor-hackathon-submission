import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

"""
Push Phase 1 lesson outputs to Supabase.

Reads OUTPUT_LESSONS/<sessionId>.json and upserts into:
  - lessons (session_id, title, uploaded_at, analysis, transcript_content jsonb)

Env:
  SUPABASE_URL, SUPABASE_KEY (service or anon key with insert rights)

Schema expected (run this SQL in Supabase SQL Editor):

  -- Ensure lessons table has all required columns
  alter table public.lessons add column if not exists analysis text;
  alter table public.lessons add column if not exists transcript_content jsonb;
  alter table public.lessons add column if not exists transcript_file text;

  -- Create lessons table if it doesn't exist
  create table if not exists public.lessons (
    id uuid primary key default gen_random_uuid(),
    session_id text unique not null,
    title text,
    uploaded_at timestamptz,
    analysis text,
    transcript_content jsonb,
    transcript_file text,
    created_at timestamptz default now()
  );

  -- Index for performance
  create index if not exists idx_lessons_session_id on public.lessons(session_id);

  -- Optional: Clear the transcripts table if you want to remove individual rows
  -- truncate table public.transcripts;
  -- drop table if exists public.transcripts;
"""

BASE = Path(__file__).resolve().parent
LESSONS_DIR = BASE / 'OUTPUT_LESSONS'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit('Missing SUPABASE_URL or SUPABASE_KEY in environment')


def sb_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }


def clear_transcripts_table():
    """Clear all entries from the transcripts table."""
    try:
        r = requests.delete(
            f"{SUPABASE_URL}/rest/v1/transcripts",
            headers=sb_headers(), timeout=30
        )
        if r.status_code in (200, 204):
            print("  ✅ Cleared transcripts table")
        else:
            print(f"  ⚠️ Could not clear transcripts table: {r.status_code}")
    except Exception as e:
        print(f"  ⚠️ Transcripts table may not exist or is already empty: {e}")


def upsert_lesson(obj):
    """Upsert lesson metadata with full transcript content as jsonb backup."""
    session_id = obj.get('sessionId')
    
    # Check if lesson already exists
    check = requests.get(
        f"{SUPABASE_URL}/rest/v1/lessons?session_id=eq.{session_id}&select=id",
        headers=sb_headers(), timeout=30
    )
    
    existing = check.json()
    
    payload = {
        'session_id': session_id,
        'title': obj.get('title'),
        'uploaded_at': obj.get('uploadedAt'),
        'analysis': obj.get('analysis'),  # AI-generated evaluation based on teaching plan
        'transcript_content': obj.get('transcript'),  # Full transcript as jsonb backup
        'transcript_file': f"{session_id}.json"  # Reference file name
    }
    
    if existing:
        # UPDATE existing record
        lesson_id = existing[0]['id']
        headers = sb_headers()
        headers['Prefer'] = 'return=representation'
        
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/lessons?session_id=eq.{session_id}",
            headers=headers, json=payload, timeout=60
        )
        
        if r.status_code not in (200, 204):
            raise RuntimeError(f"Lesson update failed: {r.status_code} {r.text}")
        
        return lesson_id
    else:
        # INSERT new record
        headers = sb_headers()
        headers['Prefer'] = 'return=representation'
        
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/lessons",
            headers=headers, json=[payload], timeout=60
        )
        
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Lesson insert failed: {r.status_code} {r.text}")
        
        data = r.json()
        return data[0]['id']


# No longer needed - transcript content is stored as jsonb in lessons table


def main():
    files = list(LESSONS_DIR.glob('*.json'))
    if not files:
        print(f"❌ No lesson files found in {LESSONS_DIR}")
        return
    
    print(f"📦 Found {len(files)} lesson(s) to push to Supabase\n")
    
    # Clear transcripts table once at the start
    print("🗑️ Clearing transcripts table...")
    clear_transcripts_table()
    print()
    
    for idx, f in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Processing {f.name}...")
        
        try:
            with f.open('r', encoding='utf-8') as fp:
                obj = json.load(fp)
        except Exception as e:
            print(f"  ❌ Failed to read file: {e}")
            continue
        
        session_id = obj.get('sessionId')
        if not session_id:
            print(f"  ⚠️ Skipping: no sessionId found")
            continue
        
        try:
            # Upsert lesson with full transcript as jsonb
            transcript = obj.get('transcript') or []
            print(f"  ⬆️ Upserting lesson with {len(transcript)} transcript entries as jsonb...")
            lesson_id = upsert_lesson(obj)
            print(f"  ✅ Lesson upserted (ID: {lesson_id})")
            print(f"  ✅ Completed {session_id}\n")
            
        except Exception as e:
            print(f"  ❌ Error processing {session_id}: {e}\n")
            continue
    
    print("🏁 Push to Supabase complete!")


if __name__ == '__main__':
    main()


