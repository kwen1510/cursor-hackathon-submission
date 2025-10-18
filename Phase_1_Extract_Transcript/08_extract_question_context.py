#!/usr/bin/env python3
"""
Phase 3 - Step 2: Extract Question Context
Extracts teacher questions with the next 2 consecutive segments for context.
"""

import json
import os
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
INPUT_LESSONS_DIR = SCRIPT_DIR / "OUTPUT_LESSONS"
OUTPUT_CONTEXT_DIR = SCRIPT_DIR / "OUTPUT_QUESTION_CONTEXT"

# Create output directory
OUTPUT_CONTEXT_DIR.mkdir(exist_ok=True)


def extract_question_contexts(transcript):
    """
    Extract teacher questions with next 2 segments as context.
    
    Args:
        transcript: List of transcript segments
        
    Returns:
        list: Question contexts with following segments
    """
    question_contexts = []
    
    for i, segment in enumerate(transcript):
        # Check if this is a teacher segment with a question
        if segment.get("role") == "TEACHER" and "?" in segment.get("text", ""):
            # Get next 2 segments (or as many as available)
            next_segments = []
            for j in range(1, 3):  # Next 2 segments
                if i + j < len(transcript):
                    next_segments.append(transcript[i + j])
            
            question_contexts.append({
                "question_index": len(question_contexts),
                "question_segment": {
                    "speaker": segment.get("speaker"),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text"),
                    "role": segment.get("role")
                },
                "next_segments": next_segments
            })
    
    return question_contexts


def process_lesson(lesson_path):
    """
    Process a single lesson file and extract question contexts.
    
    Args:
        lesson_path: Path to lesson JSON file
        
    Returns:
        dict: Question context data
    """
    print(f"\nProcessing: {lesson_path.name}")
    
    with open(lesson_path, 'r', encoding='utf-8') as f:
        lesson_data = json.load(f)
    
    transcript = lesson_data.get("transcript", [])
    session_id = lesson_data.get("sessionId")
    title = lesson_data.get("title", "Untitled")
    
    question_contexts = extract_question_contexts(transcript)
    
    result = {
        "sessionId": session_id,
        "title": title,
        "question_contexts": question_contexts,
        "total_questions": len(question_contexts)
    }
    
    print(f"  ✓ Extracted {len(question_contexts)} question contexts")
    
    return result


def main():
    """Main function to process all lesson files."""
    print("=" * 60)
    print("PHASE 3 - STEP 2: EXTRACT QUESTION CONTEXT")
    print("=" * 60)
    
    # Find all lesson files
    lesson_files = list(INPUT_LESSONS_DIR.glob("*.json"))
    
    if not lesson_files:
        print(f"\n❌ No lesson files found in {INPUT_LESSONS_DIR}")
        return
    
    print(f"\nFound {len(lesson_files)} lesson file(s)")
    
    # Process each file
    for lesson_file in lesson_files:
        try:
            result = process_lesson(lesson_file)
            
            # Save output
            output_file = OUTPUT_CONTEXT_DIR / f"{result['sessionId']}_context.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved to: {output_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error processing {lesson_file.name}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✓ Question context extraction complete!")
    print(f"✓ Output saved to: {OUTPUT_CONTEXT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

