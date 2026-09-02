-- Employee Monitor Database Schema
-- Run this in the Supabase SQL Editor

-- PHASE 2: Computers Table

CREATE TABLE IF NOT EXISTS public.computers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT NOT NULL,
    employee_name TEXT,
    status TEXT NOT NULL DEFAULT 'offline',
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    agent_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.computers ENABLE ROW LEVEL SECURITY;

-- Create policy to allow authenticated users (admin) to read and update
CREATE POLICY "Enable read access for authenticated users" 
ON public.computers FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Enable update access for authenticated users" 
ON public.computers FOR UPDATE 
TO authenticated 
USING (true);

CREATE POLICY "Enable insert access for authenticated users" 
ON public.computers FOR INSERT 
TO authenticated 
WITH CHECK (true);

CREATE POLICY "Enable delete access for authenticated users" 
ON public.computers FOR DELETE 
TO authenticated 
USING (true);

-- Note: The Python backend uses the service_role key, so it bypasses RLS.
-- RLS is only strictly necessary if we access the DB directly from the frontend.
-- For the frontend admin dashboard, they will log in with Supabase Auth,
-- so the authenticated role will have access.
