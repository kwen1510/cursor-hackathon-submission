# AI Teaching Assistant

An automated system that helps teachers improve their teaching practice through AI-powered analysis and personalised research.

## What It Does

This tool provides teachers with **three levels of support**:

1. **Process Data** - Automatically transcribe and analyze classroom recordings
2. **Quick, Actionable Feedback** - Get immediate teaching tips via email
3. **Deep Analysis** - Deep-dive into personalised teaching strategies using AI

## How It Works

### Onboarding
- Web interface for teachers to set goals and gather research to ground practice
- Teachers set improvement goals, AI researches best practices
- **Manus AI** conducts deep research on teaching strategies
- Results delivered via email webhook

### Phase 1: Automated Processing (On-Prem CRON Jobs)
- Integrates with **Panopto** video systems via CRON jobs
- Automatically processes classroom recordings when uploaded
- Uses **ElevenLabs** for speaker diarization and transcription
- **Anthropic Claude** analyzes teaching effectiveness
- **Groq Whisper** provides fast speech-to-text inference
- Sends immediate, actionable feedback via email (Google Apps Script)

### Phase 2: Deep Dive Application
- Web interface for teachers who want to explore further
- Optional detailed analysis of transcripts, pedagogy patterns, and engagement metrics

## Key Features

**Email-First Communication**
- Immediate feedback after each lesson
- Manus AI research results delivered to inbox
- No need to log in unless you want details

**Intelligent Analysis**
- Question type classification (cold-call, warm-call, whole-class, etc.)
- Teaching strategy identification
- Personalised improvement recommendations

**Optional Deep Dive**
- Review full transcripts with timestamps
- Flag important moments for reflection
- View detailed pedagogy analysis
- Track improvement over time

## Technology Stack

- **Anthropic Claude** - The brain behind all analysis
- **ElevenLabs** - High-quality transcription and speaker diarization
- **Groq Whisper** - Fast speech-to-text inference
- **Manus AI** - Deep research on teaching strategies
- **Supabase** - Unified database connecting on-prem to web interface
- **Google Apps Script** - Email delivery system

## Quick Start

### Phase 1 (Automated Processing)
1. Configure `.env` with your API keys
2. Place video files in `Phase_1_Extract_Transcript/VIDEOS/`
3. Run: `python Phase_1_Extract_Transcript/00_FULL_PIPELINE.py`
4. Receive email feedback automatically

### Phase 2 (Web Application)
1. Install dependencies: `npm install`
2. Start server: `node Phase_2_Online_Application/server.js`
3. Access at `http://localhost:3000`
4. Set teaching goals and get AI research

## Setup

Create a `.env` file with your API keys:

```bash
# Required
ELEVENLABS_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
TEACHER_EMAIL=your_email
APPSCRIPT_EMAIL=your_google_script_url

# Optional (for advanced features)
GROQ_API_KEY=your_key
MANUS_API_KEY=your_key
```

## Architecture

**On-Premises Automation**
- CRON jobs monitor Panopto uploads
- Automatic processing pipeline
- Email feedback within minutes

**Unified Data Layer**
- Supabase stores all states (flags, feedback, analysis)
- Seamless integration between automation and web interface
- Teachers access same data across platforms

**Email-Centric Design**
- Primary communication channel
- Reduces friction for busy teachers
- Optional web interface for deep dives

## Use Cases

**For Busy Teachers**
- Decide their plans for the terms once, and ground it on sound resarch
- Get quick feedback via email
- No login required for basic insights
- Act on suggestions immediately

**For Reflective Teachers**
- Set improvement goals
- Ask pedagogical questions about lessons conducted
- Deep dive into pedagogy patterns

**For Teaching Coaches**
- Monitor multiple teachers
- Track improvement over time
- Share best practices