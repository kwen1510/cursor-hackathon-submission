import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

"""
Send email feedback to teacher after lesson analysis.

Reads the most recent lesson analysis and sends a concise email
with key feedback points and a link to the full analysis.

Env vars required:
  TEACHER_EMAIL - Email address to send feedback to
  APPSCRIPT_EMAIL - Google Apps Script webhook URL for sending emails
  APP_BASE_URL - Base URL of the web application
"""

BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / 'OUTPUT_LESSONS'
ANALYSIS_DIR = BASE_DIR / 'OUTPUT_ANALYSIS'

# Configuration - all required from environment
TEACHER_EMAIL = os.getenv('TEACHER_EMAIL')
WEB_APP_URL = os.getenv('APPSCRIPT_EMAIL')
APP_BASE_URL = os.getenv('APP_BASE_URL')

# Validate environment variables
if not TEACHER_EMAIL:
    raise EnvironmentError("TEACHER_EMAIL environment variable is required")
if not WEB_APP_URL:
    raise EnvironmentError("APPSCRIPT_EMAIL environment variable is required")
if not APP_BASE_URL:
    raise EnvironmentError("APP_BASE_URL environment variable is required")


def read_json(path: Path):
    """Read JSON file."""
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def read_analysis(path: Path):
    """Read analysis markdown file."""
    return path.read_text(encoding='utf-8')


def extract_summary_from_analysis(analysis_text: str) -> dict:
    """
    Extract key summary points from analysis markdown.
    Returns dict with: went_well, work_on, next_step
    """
    lines = analysis_text.split('\n')
    
    summary = {
        'went_well': '',
        'work_on': '',
        'next_step': ''
    }
    
    current_section = None
    content_buffer = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect sections
        if 'what went well' in line_lower:
            if current_section and content_buffer:
                summary[current_section] = '\n'.join(content_buffer).strip()
            current_section = 'went_well'
            content_buffer = []
        elif 'what to work on' in line_lower or 'work on' in line_lower:
            if current_section and content_buffer:
                summary[current_section] = '\n'.join(content_buffer).strip()
            current_section = 'work_on'
            content_buffer = []
        elif 'next step' in line_lower:
            if current_section and content_buffer:
                summary[current_section] = '\n'.join(content_buffer).strip()
            current_section = 'next_step'
            content_buffer = []
        elif current_section and line.strip() and not line.startswith('#'):
            content_buffer.append(line)
    
    # Save last section
    if current_section and content_buffer:
        summary[current_section] = '\n'.join(content_buffer).strip()
    
    return summary


def create_email_html(summary: dict, session_id: str, teacher_name: str = "Teacher") -> str:
    """
    Create HTML email body from analysis summary.
    """
    app_url = f"{APP_BASE_URL}/?sessionId={session_id}"
    
    # Extract just the first key point from each section for brevity
    went_well = summary.get('went_well', '').split('\n')[0] if summary.get('went_well') else 'Great lesson today!'
    next_step = summary.get('next_step', '').split('\n')[0] if summary.get('next_step') else 'Keep up the good work!'
    
    # Clean up formatting
    went_well = went_well.strip('- ').strip()
    next_step = next_step.strip('- ').strip()
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb; margin-bottom: 24px;">🎓 Lesson Feedback Report</h2>
        
        <p style="color: #1f2937; font-size: 16px; line-height: 1.5;">Hi {teacher_name},</p>
        
        <div style="background-color: #f3f4f6; border-left: 4px solid #10b981; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="color: #065f46; margin: 0; font-weight: 500;">✨ {went_well}</p>
        </div>
        
        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="color: #92400e; margin: 0;"><strong>💡 Next Step:</strong> {next_step}</p>
        </div>
        
        <p style="color: #1f2937; font-size: 14px; line-height: 1.5; margin-top: 24px;">
            View your complete lesson analysis and transcript 
            <a href="{app_url}" style="color: #2563eb; text-decoration: none; font-weight: 500;">here →</a>
        </p>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        
        <p style="color: #6b7280; font-size: 12px; line-height: 1.5;">
            This is an automated feedback email generated from your classroom recording.
        </p>
    </div>
    """
    
    return html


def send_email(to_email: str, subject: str, html_body: str):
    """Send email via Google Apps Script webhook."""
    payload = {
        "to": to_email,
        "subject": subject,
        "htmlBody": html_body
    }
    
    try:
        response = requests.post(
            WEB_APP_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=15
        )
        response.raise_for_status()
        return True, response.text
    except Exception as e:
        return False, str(e)


def main():
    print("📧 Email Feedback System")
    print("=" * 50)
    
    # Find all lesson files
    lesson_files = sorted(LESSONS_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not lesson_files:
        print(f"❌ No lesson files found in {LESSONS_DIR}")
        return
    
    print(f"\n📋 Found {len(lesson_files)} lesson(s) to email")
    
    for lesson_path in lesson_files:
        session_id = lesson_path.stem
        analysis_path = ANALYSIS_DIR / f"{session_id}_analysis.md"
        
        print(f"\n📨 Processing lesson: {session_id}")
        
        # Check if analysis exists
        if not analysis_path.exists():
            print(f"   ⚠️  No analysis found at {analysis_path} - skipping")
            continue
        
        # Read lesson data
        lesson_data = read_json(lesson_path)
        
        # Check if email already sent
        if lesson_data.get('email_sent'):
            print(f"   ℹ️  Email already sent for this lesson - skipping")
            continue
        
        # Read and parse analysis
        analysis_text = read_analysis(analysis_path)
        summary = extract_summary_from_analysis(analysis_text)
        
        # Get teacher name from metadata if available
        teacher_name = lesson_data.get('metadata', {}).get('teacher_name', 'Teacher')
        
        # Create email HTML
        html_body = create_email_html(summary, session_id, teacher_name)
        
        # Send email
        print(f"   📤 Sending email to {TEACHER_EMAIL}...")
        success, message = send_email(
            TEACHER_EMAIL,
            "Lesson Feedback Report",
            html_body
        )
        
        if success:
            print(f"   ✅ Email sent successfully!")
            print(f"   Response: {message}")
            
            # Mark as sent in lesson data
            lesson_data['email_sent'] = True
            lesson_data['email_sent_to'] = TEACHER_EMAIL
            
            with lesson_path.open('w', encoding='utf-8') as f:
                json.dump(lesson_data, f, ensure_ascii=False, indent=2)
        else:
            print(f"   ❌ Failed to send email: {message}")
    
    print("\n🏁 Email sending complete!")


if __name__ == '__main__':
    main()

