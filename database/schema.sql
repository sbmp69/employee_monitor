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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    blocked_websites TEXT[] DEFAULT '{}',
    policy_status TEXT DEFAULT 'Unconfigured'
);

-- PHASE 4: Recordings Table
CREATE TABLE IF NOT EXISTS public.recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES public.computers(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PHASE 6: Audit Logs
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action TEXT NOT NULL,
    admin_email TEXT,
    target_device_id UUID REFERENCES public.computers(id) ON DELETE SET NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.computers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Policies for Computers
CREATE POLICY "Enable read access for authenticated users" ON public.computers FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable update access for authenticated users" ON public.computers FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Enable insert access for authenticated users" ON public.computers FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable delete access for authenticated users" ON public.computers FOR DELETE TO authenticated USING (true);

-- Policies for Recordings
CREATE POLICY "Enable read access for authenticated users" ON public.recordings FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable insert access for authenticated users" ON public.recordings FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable delete access for authenticated users" ON public.recordings FOR DELETE TO authenticated USING (true);

-- Policies for Audit Logs
CREATE POLICY "Enable read access for authenticated users" ON public.audit_logs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable insert access for authenticated users" ON public.audit_logs FOR INSERT TO authenticated WITH CHECK (true);
