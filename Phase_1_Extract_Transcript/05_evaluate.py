import os
import json
from pathlib import Path
import time
import requests
from dotenv import load_dotenv

load_dotenv()

"""
Evaluate lessons using personalized teaching plans from Supabase.

Fetches the most recent completed onboarding session for the teacher,
extracts their goals and research-backed strategies, then evaluates
lesson transcripts against these personalized criteria.

Reads Phase 1 OUTPUT_LESSONS/<sessionId>.json, creates a detailed
evaluation markdown, and writes:
  - OUTPUT_ANALYSIS/<sessionId>_analysis.md
  - Updates OUTPUT_LESSONS/<sessionId>.json to include { analysis: ... }

Env vars required:
  ANTHROPIC_API_KEY
  SUPABASE_URL
  SUPABASE_SERVICE_KEY

Model used: claude-sonnet-4-5-20250929
"""

BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / 'OUTPUT_LESSONS'
ANALYSIS_DIR = BASE_DIR / 'OUTPUT_ANALYSIS'
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_MODEL = 'claude-sonnet-4-5-20250929'

# Teacher email from environment variable
TEACHER_EMAIL = os.getenv('TEACHER_EMAIL')
if not TEACHER_EMAIL:
    raise EnvironmentError("TEACHER_EMAIL environment variable is required")


def read_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def transcript_to_text(transcript):
    """Convert transcript array to timestamped text format."""
    parts = []
    for t in transcript:
        start = int(float(t.get('start', 0)))
        h = start // 3600
        m = (start % 3600) // 60
        s = start % 60
        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        role = (t.get('role') or '').upper() or 'SPEAKER'
        text = t.get('text') or ''
        parts.append(f"[{ts}] {role}: {text}")
    return "\n".join(parts)


def fetch_markdown_content(url: str) -> str:
    """Fetch markdown file content from URL."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"   ⚠️  Failed to fetch markdown from {url[:50]}...: {e}")
        return ""


def fetch_teaching_plan():
    """
    Fetch the most recent completed onboarding session from Supabase.
    Downloads and includes content from markdown research files.
    Returns dict with: goal_text, research_output, research_sources, research_files_content
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("⚠️  Missing SUPABASE_URL or SUPABASE_SERVICE_KEY - skipping teaching plan")
        return None
    
    try:
        print(f"📡 Fetching teaching plan for {TEACHER_EMAIL}...")
        
        url = f"{SUPABASE_URL}/rest/v1/onboarding_sessions"
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Query for most recent completed session
        params = {
            'user_email': f'eq.{TEACHER_EMAIL}',
            'status': 'eq.completed',
            'select': 'id,goal_text,research_output,research_sources,created_at',
            'order': 'created_at.desc',
            'limit': '1'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        sessions = response.json()
        if not sessions:
            print(f"⚠️  No completed teaching plans found for {TEACHER_EMAIL}")
            return None
        
        session = sessions[0]
        print(f"✅ Found teaching plan (ID: {session.get('id')})")
        print(f"   Created: {session.get('created_at')}")
        
        # Fetch actual markdown file contents from URLs
        research_sources = session.get('research_sources', [])
        research_files_content = {}
        
        if research_sources:
            print(f"📥 Downloading {len(research_sources)} research file(s)...")
            for source in research_sources:
                filename = source.get('file_name', 'unknown')
                url = source.get('url', '')
                if url:
                    print(f"   ⬇️  Fetching {filename}...")
                    content = fetch_markdown_content(url)
                    if content:
                        research_files_content[filename] = content
                        print(f"   ✅ Downloaded {filename} ({len(content)} chars)")
        
        return {
            'goal_text': session.get('goal_text', ''),
            'research_output': session.get('research_output', ''),
            'research_sources': research_sources,
            'research_files_content': research_files_content
        }
        
    except Exception as e:
        print(f"❌ Failed to fetch teaching plan: {e}")
        return None


def create_evaluation_prompt(teaching_plan):
    """
    Create a detailed evaluation prompt incorporating the teacher's
    personalized goals and research-backed strategies.
    """
    if not teaching_plan:
        # Fallback to generic analysis if no teaching plan available
        return """You are an expert pedagogy analyst.

Task: Analyze a classroom lesson transcript. Provide:
- Key learning objectives inferred
- Teaching strategies observed (questioning, scaffolding, formative assessment)
- Student engagement signals and moments
- Misconceptions or confusion points
- Actionable feedback for the teacher (3-5 bullets)
- Notable quotes with timestamps

Voice: concise, specific, constructive. Use timestamps in [mm:ss] or [hh:mm:ss] format.

Constraints:
- Be objective and avoid speculation beyond transcript evidence
- Prefer past tense when describing what occurred
- CRITICAL: Use ONLY single timestamps like [mm:ss] or [hh:mm:ss]
- NEVER use timestamp ranges like [mm:ss-mm:ss] or [00:00-07:37]
- Each piece of evidence should have ONE clickable timestamp only"""

    goal_text = teaching_plan.get('goal_text', '').strip()
    research_output = teaching_plan.get('research_output', '').strip()
    sources_count = len(teaching_plan.get('research_sources', []))
    research_files_content = teaching_plan.get('research_files_content', {})
    
    # Build research section with full content from markdown files
    research_section = f"{research_output if research_output else 'No research strategies available.'}"
    
    if research_files_content:
        research_section += "\n\n" + "─" * 50 + "\nDETAILED RESEARCH FILES\n" + "─" * 50
        for filename, content in research_files_content.items():
            research_section += f"\n\n### {filename}\n\n{content[:8000]}"  # Limit to 8000 chars per file
    
    prompt = f"""You are an expert pedagogy analyst with access to this teacher's professional development goals and research-backed recommendations.

═══════════════════════════════════════════════════
TEACHER'S PROFESSIONAL DEVELOPMENT PLAN
═══════════════════════════════════════════════════

{goal_text if goal_text else "No specific goals recorded."}

═══════════════════════════════════════════════════
RESEARCH-BACKED STRATEGIES (Based on {sources_count} academic sources)
═══════════════════════════════════════════════════

{research_section}

═══════════════════════════════════════════════════
YOUR EVALUATION TASK
═══════════════════════════════════════════════════

Analyze the lesson transcript through the lens of the teacher's goals and research strategies above.

**Keep it concise and chill.** Focus on what matters most:

**Format:**

**What Went Well (1-2 points max)**
Pick the 1-2 most notable strengths you observed. Include one timestamp [mm:ss] as evidence.

**What to Work On (1-2 points max)**
Identify 1-2 key areas where the teacher's goals aren't quite being met yet. Include one timestamp [mm:ss] as evidence. Keep it constructive and specific.

**Next Step**
One simple, actionable suggestion they can try in their very next lesson. Make it concrete and easy to implement - something they can do tomorrow.

Voice: friendly, supportive, practical
Length: Keep total response under 200 words - be concise!

CRITICAL CONSTRAINTS:
- Use ONLY single timestamps like [mm:ss] or [hh:mm:ss]
- NEVER use timestamp ranges
- Be specific but brief
- Focus on what's most important, not everything"""

    return prompt


def anthropic_request(prompt: str, content: str) -> str:
    """Make a request to Anthropic API."""
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError('Missing ANTHROPIC_API_KEY')
    
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    payload = {
        'model': ANTHROPIC_MODEL,
        'max_tokens': 800,  # Reduced for concise evaluation (targeting ~200 words)
        'system': prompt,
        'messages': [
            { 'role': 'user', 'content': content }
        ]
    }
    r = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    blocks = data.get('content') or []
    out = []
    for b in blocks:
        if isinstance(b, dict) and b.get('type') == 'text':
            out.append(b.get('text', ''))
    return "".join(out).strip()


def chunk_text(s: str, max_chars: int = 12000):
    """Chunk text for API processing."""
    if len(s) <= max_chars:
        return [s]
    chunks, i = [], 0
    while i < len(s):
        chunks.append(s[i:i+max_chars])
        i += max_chars
    return chunks


def evaluate_lesson_file(path: Path, teaching_plan) -> str:
    """
    Evaluate a lesson transcript using the personalized teaching plan.
    Returns path to the generated analysis markdown file.
    """
    data = read_json(path)
    transcript = data.get('transcript') or []
    raw_text = transcript_to_text(transcript)
    chunks = chunk_text(raw_text)
    
    system_prompt = create_evaluation_prompt(teaching_plan)
    
    partial_analyses = []
    for idx, ch in enumerate(chunks, start=1):
        content = f"Lesson transcript chunk {idx}/{len(chunks)}:\n\n{ch}"
        partial = anthropic_request(system_prompt, content)
        partial_analyses.append(partial)
        time.sleep(0.4)
    
    if len(partial_analyses) == 1:
        final_analysis = partial_analyses[0]
    else:
        joined = "\n\n---\n\n".join(partial_analyses)
        final_analysis = anthropic_request(
            system_prompt,
            f"Merge these partial evaluations into one cohesive, comprehensive analysis. Maintain the structured format and deduplicate evidence:\n\n{joined}"
        )
    
    # Save MD and update lesson JSON
    session_id = data.get('sessionId')
    out_md = ANALYSIS_DIR / f"{session_id}_analysis.md"
    out_md.write_text(final_analysis, encoding='utf-8')
    
    data['analysis'] = final_analysis
    write_json(path, data)
    
    return str(out_md)


def main():
    print("🎯 Lesson Evaluation System (Personalized)")
    print("=" * 50)
    
    # Fetch teaching plan once for all lessons
    teaching_plan = fetch_teaching_plan()
    
    if teaching_plan:
        print(f"\n📋 Using personalized teaching plan")
        print(f"   Goal: {teaching_plan['goal_text'][:100]}..." if teaching_plan['goal_text'] else "   No goal text")
        print(f"   Research strategies: {'Available' if teaching_plan['research_output'] else 'Not available'}")
        print(f"   Sources: {len(teaching_plan.get('research_sources', []))} files")
    else:
        print("\n⚠️  No teaching plan found - using generic analysis")
    
    print("\n" + "=" * 50)
    
    files = [p for p in LESSONS_DIR.glob('*.json')]
    if not files:
        print(f"❌ No lesson files found in {LESSONS_DIR}")
        return
    
    for f in files:
        print(f"\n🧠 Evaluating {f.name}...")
        md_path = evaluate_lesson_file(f, teaching_plan)
        print(f"✅ Analysis written to {md_path}")
    
    print("\n🏁 Evaluation complete!")
    print(f"📁 Analysis files saved to: {ANALYSIS_DIR}")


if __name__ == '__main__':
    main()

