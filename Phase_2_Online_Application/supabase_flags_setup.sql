-- Create flags table for flagging feature
-- Run this in Supabase SQL Editor

create table if not exists public.flags (
  id uuid primary key default gen_random_uuid(),
  lesson_id uuid references public.lessons(id) on delete cascade,
  session_id text not null,
  timestamp int not null,
  text text,
  speaker text,
  role text,
  note text,
  created_at timestamptz default now(),
  -- Prevent duplicate flags for same session+timestamp
  constraint unique_session_timestamp unique(session_id, timestamp)
);

-- Create indexes for performance
create index if not exists idx_flags_lesson_id on public.flags(lesson_id);
create index if not exists idx_flags_session_id on public.flags(session_id);
create index if not exists idx_flags_timestamp on public.flags(timestamp);

-- Enable Row Level Security (optional, adjust policies as needed)
alter table public.flags enable row level security;

-- Create policy for public access (adjust based on your auth requirements)
create policy "Anyone can manage flags"
  on public.flags
  for all
  using (true)
  with check (true);

