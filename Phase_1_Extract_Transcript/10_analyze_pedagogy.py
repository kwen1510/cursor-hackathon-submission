#!/usr/bin/env python3
"""
Phase 3 - Step 4: Analyze Pedagogy with Anthropic API
Uses Claude to analyze question types and identify pedagogical strategies.
"""

import json
import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

# Directories
SCRIPT_DIR = Path(__file__).parent
INPUT_PATTERNS_DIR = SCRIPT_DIR / "OUTPUT_PATTERNS"
INPUT_LESSONS_DIR = SCRIPT_DIR / "OUTPUT_LESSONS"
OUTPUT_PEDAGOGY_DIR = SCRIPT_DIR / "OUTPUT_PEDAGOGY_ANALYSIS"

# Create output directory
OUTPUT_PEDAGOGY_DIR.mkdir(exist_ok=True)

# Anthropic API setup
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_MODEL = 'claude-sonnet-4-20250514'

if not ANTHROPIC_API_KEY:
    raise SystemExit('❌ Missing ANTHROPIC_API_KEY in environment')


def call_anthropic(prompt, max_tokens=2000):
    """
    Call Anthropic API with retry logic.
    
    Args:
        prompt: User prompt
        max_tokens: Maximum tokens in response
        
    Returns:
        str: API response text
    """
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    
    payload = {
        'model': ANTHROPIC_MODEL,
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }
    
    for attempt in range(3):
        try:
            response = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data['content'][0]['text']
        except Exception as e:
            print(f"  ⚠️  API call attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                raise
    
    return None


def format_question_context(qc):
    """Format a question context for API prompt."""
    q_seg = qc.get("question_segment", {})
    next_segs = qc.get("next_segments", [])
    
    parts = [
        f"[{q_seg.get('start')}s - {q_seg.get('end')}s] {q_seg.get('role')}: {q_seg.get('text')}"
    ]
    
    for seg in next_segs:
        parts.append(f"[{seg.get('start')}s - {seg.get('end')}s] {seg.get('role')}: {seg.get('text')}")
    
    return "\n".join(parts)


def analyze_question_batch(question_contexts, pattern_type):
    """
    Analyze a batch of questions (Pass 1 & 2).
    
    Args:
        question_contexts: List of question contexts
        pattern_type: "Teacher>Student" or "Teacher>Teacher>Student"
        
    Returns:
        list: Analyzed questions
    """
    if not question_contexts:
        return []
    
    print(f"  📊 Analyzing {len(question_contexts)} {pattern_type} questions...")
    
    # Batch questions for efficiency (max 10 per call)
    batch_size = 10
    all_results = []
    
    for i in range(0, len(question_contexts), batch_size):
        batch = question_contexts[i:i+batch_size]
        
        # Format batch for prompt
        formatted_questions = []
        for idx, qc in enumerate(batch):
            formatted_questions.append(f"Question {idx + 1}:\n{format_question_context(qc)}")
        
        questions_text = "\n\n".join(formatted_questions)
        
        prompt = f"""Analyze these teacher questions from a classroom transcript. For each question, identify:
1. The topic/subject matter being discussed
2. The question type (choose ONE: cold-call, warm-call, rhetorical, hand-raising, whole-class)

Question Types:
- cold-call: Teacher calls on specific student by name
- warm-call: Teacher calls on student after giving prep time
- rhetorical: Question asked without expecting answer, teacher continues
- hand-raising: Teacher asks for volunteers
- whole-class: Open question to entire class

Pattern: {pattern_type}

Questions to analyze:

{questions_text}

Return ONLY a valid JSON array with this exact structure (no other text):
[
  {{
    "question_number": 1,
    "topic": "brief topic description",
    "question_type": "one of the types above"
  }},
  ...
]"""

        try:
            response = call_anthropic(prompt, max_tokens=4000)
            
            # Parse JSON response
            # Extract JSON from response (in case there's extra text)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                batch_results = json.loads(json_str)
                
                # Match results back to question contexts
                for j, result in enumerate(batch_results):
                    if j < len(batch):
                        qc = batch[j]
                        all_results.append({
                            "question_index": qc.get("question_index"),
                            "topic": result.get("topic", "Unknown"),
                            "question_type": result.get("question_type", "unknown"),
                            "start_timestamp": qc.get("question_segment", {}).get("start"),
                            "end_timestamp": qc.get("question_segment", {}).get("end"),
                            "question_text": qc.get("question_segment", {}).get("text", "")[:200]
                        })
            else:
                print(f"  ⚠️  Could not parse JSON from API response")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ⚠️  Error analyzing batch: {e}")
            continue
    
    return all_results


def analyze_overall_pedagogy(transcript):
    """
    Analyze overall pedagogical strategies (Pass 3).
    
    Args:
        transcript: Full lesson transcript
        
    Returns:
        dict: Overall pedagogy analysis
    """
    print(f"  🎓 Analyzing overall pedagogy...")
    
    # Format transcript
    transcript_text = []
    for seg in transcript[:50]:  # Limit to first 50 segments for API limits
        transcript_text.append(f"[{seg.get('start')}s] {seg.get('role')}: {seg.get('text', '')[:300]}")
    
    transcript_str = "\n".join(transcript_text)
    
    prompt = f"""Analyze this classroom transcript and identify the teaching pedagogies used.

Teaching Pedagogies to look for:
- Think-pair-share: Students think individually, discuss with partner, then share
- Whole-class discussion: Teacher facilitates discussion with entire class
- Hand raise: Students volunteer answers by raising hands
- Cold call: Teacher calls on specific students without hand-raising
- Practice: Students work on problems/exercises
- Exit ticket: Quick assessment at end of lesson
- Brainstorm: Rapid idea generation
- Jigsaw: Students become experts then teach peers
- Peer teaching: Students explain to other students
- Role play: Students act out scenarios
- Debate: Structured argument with positions

Transcript (first 50 segments):

{transcript_str}

Return ONLY a valid JSON object with this exact structure (no other text):
{{
  "pedagogies_identified": [
    {{
      "pedagogy": "pedagogy name",
      "frequency": "high/medium/low",
      "evidence": "specific evidence with timestamps"
    }}
  ],
  "key_strategies": ["strategy 1", "strategy 2"],
  "summary": "brief summary of teaching approach"
}}"""

    try:
        response = call_anthropic(prompt, max_tokens=3000)
        
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        else:
            print(f"  ⚠️  Could not parse JSON from API response")
            return {
                "pedagogies_identified": [],
                "key_strategies": [],
                "summary": "Analysis unavailable"
            }
    except Exception as e:
        print(f"  ⚠️  Error in overall pedagogy analysis: {e}")
        return {
            "pedagogies_identified": [],
            "key_strategies": [],
            "summary": f"Error: {str(e)}"
        }


def process_lesson(pattern_path, lesson_path):
    """
    Process a single lesson and perform all 3 analysis passes.
    
    Args:
        pattern_path: Path to patterns JSON file
        lesson_path: Path to lesson JSON file
        
    Returns:
        dict: Complete pedagogy analysis
    """
    session_id = pattern_path.stem.replace('_patterns', '')
    print(f"\n{'='*60}")
    print(f"Analyzing: {session_id}")
    print(f"{'='*60}")
    
    # Load patterns
    with open(pattern_path, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Load full lesson for transcript
    with open(lesson_path, 'r', encoding='utf-8') as f:
        lesson = json.load(f)
    
    transcript = lesson.get("transcript", [])
    
    # Pass 1: Analyze Teacher > Student questions
    teacher_student_analysis = analyze_question_batch(
        patterns.get("teacher_student", []),
        "Teacher>Student"
    )
    
    # Pass 2: Analyze Teacher > Teacher > Student questions
    teacher_teacher_student_analysis = analyze_question_batch(
        patterns.get("teacher_teacher_student", []),
        "Teacher>Teacher>Student"
    )
    
    # Pass 3: Analyze other patterns (if any)
    other_analysis = analyze_question_batch(
        patterns.get("other", []),
        "Other patterns"
    )
    
    # Pass 4: Overall pedagogy analysis
    overall_pedagogy = analyze_overall_pedagogy(transcript)
    
    # Count question types across all patterns
    all_questions = teacher_student_analysis + teacher_teacher_student_analysis + other_analysis
    question_type_counts = {
        "cold-call": 0,
        "warm-call": 0,
        "rhetorical": 0,
        "hand-raising": 0,
        "whole-class": 0,
        "unknown": 0
    }
    
    for q in all_questions:
        q_type = q.get("question_type", "unknown")
        if q_type in question_type_counts:
            question_type_counts[q_type] += 1
        else:
            question_type_counts["unknown"] += 1
    
    # Combine all results
    result = {
        "sessionId": patterns.get("sessionId"),
        "title": patterns.get("title"),
        "question_analysis": {
            "teacher_student": teacher_student_analysis,
            "teacher_teacher_student": teacher_teacher_student_analysis,
            "other": other_analysis,
            "summary": {
                "total_questions_analyzed": (
                    len(teacher_student_analysis) + 
                    len(teacher_teacher_student_analysis) + 
                    len(other_analysis)
                ),
                "question_type_counts": question_type_counts
            }
        },
        "overall_pedagogy": overall_pedagogy,
        "pattern_summary": patterns.get("summary", {})
    }
    
    return result


def main():
    """Main function to analyze all lessons."""
    print("=" * 60)
    print("PHASE 3 - STEP 4: ANTHROPIC PEDAGOGY ANALYSIS")
    print("=" * 60)
    
    # Find all pattern files
    pattern_files = list(INPUT_PATTERNS_DIR.glob("*_patterns.json"))
    
    if not pattern_files:
        print(f"\n❌ No pattern files found in {INPUT_PATTERNS_DIR}")
        print("   Run 03_classify_patterns.py first!")
        return
    
    print(f"\nFound {len(pattern_files)} pattern file(s)")
    print(f"Using model: {ANTHROPIC_MODEL}")
    
    # Process each file
    for pattern_file in pattern_files:
        try:
            # Find corresponding lesson file
            session_id = pattern_file.stem.replace('_patterns', '')
            lesson_file = INPUT_LESSONS_DIR / f"{session_id}.json"
            
            if not lesson_file.exists():
                print(f"\n⚠️  Lesson file not found: {lesson_file.name}")
                continue
            
            result = process_lesson(pattern_file, lesson_file)
            
            # Save output
            output_file = OUTPUT_PEDAGOGY_DIR / f"{session_id}_pedagogy.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Saved analysis to: {output_file.name}")
            print(f"  - Questions analyzed: {result['question_analysis']['summary']['total_questions_analyzed']}")
            
            # Print question type counts
            q_counts = result['question_analysis']['summary']['question_type_counts']
            print(f"  - Question types:")
            for q_type, count in q_counts.items():
                if count > 0:
                    print(f"    • {q_type}: {count}")
            
            print(f"  - Pedagogies identified: {len(result['overall_pedagogy'].get('pedagogies_identified', []))}")
            
        except Exception as e:
            print(f"\n❌ Error processing {pattern_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 60)
    print("✓ Pedagogy analysis complete!")
    print(f"✓ Output saved to: {OUTPUT_PEDAGOGY_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

