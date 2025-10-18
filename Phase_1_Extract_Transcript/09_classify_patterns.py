#!/usr/bin/env python3
"""
Phase 3 - Step 3: Classify Interaction Patterns
Classifies question-response patterns based on speaker sequences.
"""

import json
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
INPUT_CONTEXT_DIR = SCRIPT_DIR / "OUTPUT_QUESTION_CONTEXT"
OUTPUT_PATTERNS_DIR = SCRIPT_DIR / "OUTPUT_PATTERNS"

# Create output directory
OUTPUT_PATTERNS_DIR.mkdir(exist_ok=True)


def classify_pattern(question_context):
    """
    Classify interaction pattern based on speaker roles.
    
    Args:
        question_context: Dict with question_segment and next_segments
        
    Returns:
        str: Pattern type ("teacher_student", "teacher_teacher_student", "other")
    """
    next_segments = question_context.get("next_segments", [])
    
    if len(next_segments) == 0:
        return "other"
    
    # Get roles
    first_role = next_segments[0].get("role") if len(next_segments) > 0 else None
    second_role = next_segments[1].get("role") if len(next_segments) > 1 else None
    
    # Teacher > Student pattern
    if first_role == "STUDENT":
        return "teacher_student"
    
    # Teacher > Teacher > Student pattern
    if first_role == "TEACHER" and second_role == "STUDENT":
        return "teacher_teacher_student"
    
    # Everything else
    return "other"


def classify_all_patterns(context_data):
    """
    Classify all question contexts into pattern groups.
    
    Args:
        context_data: Full context data with question_contexts
        
    Returns:
        dict: Patterns grouped by type
    """
    patterns = {
        "teacher_student": [],
        "teacher_teacher_student": [],
        "other": []
    }
    
    for question_context in context_data.get("question_contexts", []):
        pattern_type = classify_pattern(question_context)
        patterns[pattern_type].append(question_context)
    
    return patterns


def process_context_file(context_path):
    """
    Process a single context file and classify patterns.
    
    Args:
        context_path: Path to context JSON file
        
    Returns:
        dict: Classified patterns
    """
    print(f"\nProcessing: {context_path.name}")
    
    with open(context_path, 'r', encoding='utf-8') as f:
        context_data = json.load(f)
    
    patterns = classify_all_patterns(context_data)
    
    result = {
        "sessionId": context_data.get("sessionId"),
        "title": context_data.get("title"),
        "teacher_student": patterns["teacher_student"],
        "teacher_teacher_student": patterns["teacher_teacher_student"],
        "other": patterns["other"],
        "summary": {
            "total_questions": context_data.get("total_questions", 0),
            "teacher_student_count": len(patterns["teacher_student"]),
            "teacher_teacher_student_count": len(patterns["teacher_teacher_student"]),
            "other_count": len(patterns["other"])
        }
    }
    
    print(f"  ✓ Teacher → Student: {result['summary']['teacher_student_count']}")
    print(f"  ✓ Teacher → Teacher → Student: {result['summary']['teacher_teacher_student_count']}")
    print(f"  ✓ Other patterns: {result['summary']['other_count']}")
    
    return result


def main():
    """Main function to process all context files."""
    print("=" * 60)
    print("PHASE 3 - STEP 3: CLASSIFY INTERACTION PATTERNS")
    print("=" * 60)
    
    # Find all context files
    context_files = list(INPUT_CONTEXT_DIR.glob("*_context.json"))
    
    if not context_files:
        print(f"\n❌ No context files found in {INPUT_CONTEXT_DIR}")
        print("   Run 02_extract_question_context.py first!")
        return
    
    print(f"\nFound {len(context_files)} context file(s)")
    
    # Process each file
    for context_file in context_files:
        try:
            result = process_context_file(context_file)
            
            # Save output
            session_id = result['sessionId']
            output_file = OUTPUT_PATTERNS_DIR / f"{session_id}_patterns.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved to: {output_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error processing {context_file.name}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✓ Pattern classification complete!")
    print(f"✓ Output saved to: {OUTPUT_PATTERNS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

