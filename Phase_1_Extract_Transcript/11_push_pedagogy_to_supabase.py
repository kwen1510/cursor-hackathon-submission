#!/usr/bin/env python3
"""
Phase 3 - Step 5: Push Pedagogy Analysis to Supabase
Updates lessons table with consolidated pedagogy analysis.
"""

import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

# Directories
SCRIPT_DIR = Path(__file__).parent
INPUT_PEDAGOGY_DIR = SCRIPT_DIR / "OUTPUT_PEDAGOGY_ANALYSIS"

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit('❌ Missing SUPABASE_URL or SUPABASE_KEY in environment')


def sb_headers():
    """Get Supabase request headers."""
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }


def update_lesson_pedagogy(session_id, pedagogy_analysis):
    """
    Update a lesson record with pedagogy analysis.
    
    Args:
        session_id: Session ID to update
        pedagogy_analysis: Pedagogy analysis data
        
    Returns:
        bool: Success status
    """
    # Check if lesson exists
    check_url = f"{SUPABASE_URL}/rest/v1/lessons?session_id=eq.{session_id}&select=id,session_id"
    check_response = requests.get(check_url, headers=sb_headers(), timeout=30)
    
    if check_response.status_code != 200:
        print(f"  ❌ Failed to check lesson existence: {check_response.status_code}")
        return False
    
    existing = check_response.json()
    
    if not existing:
        print(f"  ⚠️  Lesson not found in database: {session_id}")
        print(f"     Run Phase 1 (06_push_to_supabase.py) first to create the lesson record")
        return False
    
    # Update lesson with pedagogy analysis
    update_url = f"{SUPABASE_URL}/rest/v1/lessons?session_id=eq.{session_id}"
    payload = {
        'pedagogy_analysis': pedagogy_analysis
    }
    
    update_response = requests.patch(
        update_url,
        headers=sb_headers(),
        json=payload,
        timeout=60
    )
    
    if update_response.status_code in (200, 204):
        return True
    else:
        print(f"  ❌ Update failed: {update_response.status_code} - {update_response.text}")
        return False


def process_pedagogy_file(pedagogy_path):
    """
    Process a single pedagogy analysis file and push to Supabase.
    
    Args:
        pedagogy_path: Path to pedagogy JSON file
        
    Returns:
        bool: Success status
    """
    session_id = pedagogy_path.stem.replace('_pedagogy', '')
    print(f"\nProcessing: {session_id}")
    
    try:
        with open(pedagogy_path, 'r', encoding='utf-8') as f:
            pedagogy_data = json.load(f)
        
        print(f"  📊 Questions analyzed: {pedagogy_data.get('question_analysis', {}).get('summary', {}).get('total_questions_analyzed', 0)}")
        print(f"  🎓 Pedagogies identified: {len(pedagogy_data.get('overall_pedagogy', {}).get('pedagogies_identified', []))}")
        
        # Update Supabase
        print(f"  ⬆️  Updating Supabase...")
        success = update_lesson_pedagogy(session_id, pedagogy_data)
        
        if success:
            print(f"  ✅ Successfully updated lesson: {session_id}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {pedagogy_path.name}: {e}")
        return False


def main():
    """Main function to push all pedagogy analyses to Supabase."""
    print("=" * 60)
    print("PHASE 3 - STEP 5: PUSH PEDAGOGY TO SUPABASE")
    print("=" * 60)
    
    # Find all pedagogy analysis files
    pedagogy_files = list(INPUT_PEDAGOGY_DIR.glob("*_pedagogy.json"))
    
    if not pedagogy_files:
        print(f"\n❌ No pedagogy analysis files found in {INPUT_PEDAGOGY_DIR}")
        print("   Run 04_analyze_pedagogy.py first!")
        return
    
    print(f"\nFound {len(pedagogy_files)} pedagogy analysis file(s)")
    print(f"Supabase URL: {SUPABASE_URL}")
    
    # Process each file
    success_count = 0
    fail_count = 0
    
    for pedagogy_file in pedagogy_files:
        if process_pedagogy_file(pedagogy_file):
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully updated: {success_count}")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count}")
    print("=" * 60)
    
    if fail_count == 0:
        print("\n🎉 All pedagogy analyses pushed to Supabase!")
    else:
        print(f"\n⚠️  Some updates failed. Check the errors above.")


if __name__ == "__main__":
    main()

