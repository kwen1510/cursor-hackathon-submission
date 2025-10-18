-- Add unique constraint to prevent duplicate flags
-- Run this in Supabase SQL Editor if you already have a flags table

-- First, remove any existing duplicates
DELETE FROM public.flags a
USING public.flags b
WHERE a.id > b.id 
  AND a.session_id = b.session_id 
  AND a.timestamp = b.timestamp;

-- Then add the unique constraint
ALTER TABLE public.flags 
ADD CONSTRAINT unique_session_timestamp 
UNIQUE (session_id, timestamp);

